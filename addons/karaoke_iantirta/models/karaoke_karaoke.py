# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import logging
import traceback
from typing import Any

from sigil import _, api, fields, models
from sigil.exceptions import UserError

from ..utils import (
    LyricMetadata,
    VideoMetadata,
    extract_video_info,
    get_lyric,
    merge_log,
)

_logger = logging.getLogger(__name__)

class KaraokeKaraoke(models.Model):
    _name = 'karaoke.karaoke'
    _description = 'Karaoke Karaoke'
    _rec_name = 'title'
    _order = 'write_date desc'

    source_url = fields.Char(required=True)
    karaoke_type = fields.Selection([
        ("basic", "Basic"),
        ("plus", "Plus (Lyrics Subtitle)"),
    ], required=True, string="Karaoke Generation Type")

    _unique_source_url = models.Constraint(
        "UNIQUE(source_url)",
        "The Source Url must be unique or this url have already in database."
    )

    status = fields.Selection([
        ("waiting", "Ready"),
        ("processing", "Processing Karaoke"),
        ("completed", "Processing Completed"),
        ("failed", "Processing Failed"),
    ], default="waiting", required=True, readonly=True)
    extraction_status = fields.Selection([
        ('need_extraction', 'Extracting information'),
        ('extraction_success', 'Extracting completed.'),
        ('extraction_failed', 'Extraction failed')
    ], default='need_extraction', readonly=True)
    worker_id = fields.Many2one(
        comodel_name='gpu.worker',
        readonly=True
    )

    # Extracted Information.
    title = fields.Char(readonly=True,)
    artist = fields.Char(readonly=True, index=True)
    duration = fields.Float(readonly=True,)
    thumbnail_url = fields.Char(
        default="https://via.placeholder.com/320x180/1C1B1F/FFFFFF?text=No+Thumbnail"
    )
    lyric = fields.Text()

    download_uris = fields.Json(readonly=True)

    # Logging and debug
    error_entries = fields.Json(readonly=True)
    log_entries = fields.Json(readonly=True)
    note = fields.Text('Notes')

    # -----------------------
    # Cron method
    # -----------------------

    @api.model
    def _cron_extract_info_karaoke(self, batch_size=50):
        """
        Cron action that is not actually a scheduled, we mock this as to make it
        not running on the main thread.

        But there still error where VM not having enough memory/RAM to run script.
        especially since this is connected to yt-dlp, and its javascript code using
        either deno or node will use much more memory.

        Extracting concurrently or many many at a times
        can sometimes be a heavy process, since it require network
        and wait time.
        """        
        if to_extracts := self.search([('extraction_status', '=', 'need_extraction')]):
            commit_progress = self.env['ir.cron']._commit_progress
            commit_progress(remaining=len(to_extracts))
            
            for karaoke in to_extracts[:batch_size]:
                karaoke = karaoke.try_lock_for_update().filtered(
                    lambda d: d.extraction_status == 'need_extraction'
                )

                if not karaoke:
                    continue

                try:
                    karaoke._fetch_info()
                    karaoke.extraction_status = 'extraction_success'
                    commit_progress(1)

                except Exception as e:
                    self.env.cr.rollback()
                    _logger.error(
                        'Karaoke id(%s) information cannot be fetched. Error: %s',
                        karaoke.id, e
                    )
                    karaoke.error_entries = merge_log([('cron_extract_info_karaoke', str(type(e)), str(e), traceback.format_exc())], karaoke.error_entries)
                    karaoke.extraction_status = "extraction_failed"
                    # commit and progress even when failed
                    # Break if remaining time is less or equal 40s.
                    if commit_progress(1) > 40:
                        continue
                    else:
                        break

    # -----------------------
    # Crud Method
    # -----------------------

    @api.model_create_multi
    def create(self, vals_list):
        """
        On Karaoke Creation. we also wanted to trigger
        fetching info cron.
        """
        karaokes: KaraokeKaraoke = super().create(vals_list)

        karaokes.refetch_info()

        return karaokes

    # -----------------------
    # Actionable Method
    # -----------------------

    def _fetch_lyric_info(self):
        """
        Method that will make api call for song lyric information
        Extraction.

        Song lyric metadata also have artist, title, and sometimes much
        more accurate than video info.

        Will not fetch if needed fields already defined unless erased.
        """
        self.ensure_one()

        if not self.title or not self.artist or not self.duration:
            raise UserError(_("Fetching lyric info should be after title, artist, and duration defined."))

        # Will not fetch if lyric already defined
        if self.lyric:
            return

        metadata: LyricMetadata = get_lyric(
            self.title,
            self.artist,
            self.duration,
        )

        # Will override title, and artist information.
        self.title = metadata.trackName
        self.artist = metadata.artistName
        self.lyric = metadata.plainLyrics

        del metadata

    def _fetch_video_info(self):
        """
        Method that will make api call for song video information
        Extraction.

        Will not fetch if needed fields already defined unless erased.
        """
        self.ensure_one()

        if self.title and self.artist and self.duration and self.thumbnail_url:
            return

        metadata: VideoMetadata = extract_video_info(self.source_url)

        # Avoid unnecessary ORM
        # And will only update if not already defined.

        if not self.title:
            self.title = metadata.title

        if not self.artist:
            self.artist = metadata.resolved_artist

        if not self.duration:
            self.duration = metadata.duration

        if not self.thumbnail_url:
            self.thumbnail_url = metadata.thumbnail_url

        del metadata

    def _fetch_info(self):
        """
        Method that will make api call for both song and lyric inforation.
        Routed by field ``karaoke_type``

        Will not fetch if needed fields already defined unless erased.
        """
        self.ensure_one()

        _last_error = None

        try:
            self._fetch_video_info()
            _logger.debug(
                'Karaoke id(%s) information fetched.', self.id
            )
        except Exception as e:
            _logger.exception(
                'Karaoke id(%s) information cannot be fetched.',
                self.id
            )
            _last_error = e

        # Only fetch lyrics only if no error
        # type is ``plus`` and necesssary fields exists.
        if (
            _last_error is None
            and self.karaoke_type == 'plus'
            and self.title
            and self.artist
            and self.duration
        ):
            try:
                self._fetch_lyric_info()
                _logger.debug(
                    'Karaoke id(%s) lyric fetched.', self.id
                )
            except Exception as e:
                _logger.exception(
                    'Karaoke id(%s) Lyric cannot be fetched.',
                    self.id
                )
                _last_error = e

        if _last_error is not None:
            raise _last_error

    def _prepare_data_api(self, domain: list[tuple], *, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Called by controllers to send necessary data for processing. 
        
        Any data given by this should be common and general usage only.

        :param DomainType domain:
        :param int | None limit:
        :return: list dictionary of karaoke data
        :rtype: list[dict[str, Any]]
        """
        karaokes = self.sudo().search(domain, limit=limit)
        valid_fields = [
            'id',
            'title',
            'artist',
            'duration',
            'lyric',
            'status',
            'source_url',
            'karaoke_type',
        ]
        return [{field: karaoke[field] for field in valid_fields} for karaoke in karaokes]

    def _update_from_dict(self, **data) -> None:
        """
        Called by controllers to update necessary data after processing. 
        
        Any data given by controller should be filtered according whats needed
        and valid fields..

        :param dict[str, Any] data:
        """
        valid_fields = [
            'title',
            'artist',
            'duration',
            'thumbnail_url',
            'lyric',
            'download_uris',
            'status',
            'log_entries',
            "error_entries",
        ]
        if not (karaoke_id := data.pop("id", None)):
            raise UserError(_('Method update_from_dict require karaoke id to be passed'))

        if karaoke := self.sudo().browse(karaoke_id).exists():
            error_entries = data.pop("error_entries", [])

            # Success only if not error_entries
            # And download_uris exists.
            if not error_entries and data.get('download_uris'):
                data['status'] = 'completed'

            else:
                data['status'] = 'failed'
                data['error_entries'] = merge_log(error_entries, karaoke.error_entries)

            if log_entries := data.get('log_entries'):
                data['log_entries'] = merge_log(karaoke.log_entries, log_entries)

            karaoke.write({field: data[field] for field in valid_fields})

        else:
            raise UserError(_("karaoke id not found in the database"))

    def refetch_info(self):
        """
        Actually refetch song information.
        
        This is posting job only to cron.
        """
        self.write({'extraction_status': 'need_extraction'})

        if cron := self.env.ref('karaoke_iantirta.ir_cron_extract_info_karaoke'):
            cron._trigger()

        _logger.debug('Running extract karaoke cron %s', cron.name)

    def reset_status(self):
        """
        Reset karaoke status
        """
        self.write({
            "status": "waiting",
            "log_entries": False,
            "error_entries": False,
        })

    # -----------------------
    # User Action
    # -----------------------

    def action_refetch_info(self):
        """
        Method action to refetch info.
        """
        self.refetch_info()
        message = _("Posting refetch info %s task(s) to cron job.") % len(self)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_reset_status(self):
        """
        Method action to reset karaoke status.
        """
        self.reset_status()
        message = _("Successfully reset %s task(s).") % len(self)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
