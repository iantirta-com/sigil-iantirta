import logging
import os
import traceback

from sigil import _, api, fields, models
from sigil.exceptions import UserError
from sigil.tools import config

from ..utils import (
    LyricMetadata,
    VideoMetadata,
    extract_video_info,
    get_lyric,
    merge_log,
    netsvc,
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
        ('need_extraction', 'Extracting information'),
        ("processing", "Processing Karaoke"),
        ("completed", "Processing Completed"),
        ("failed", "Processing Failed"),
    ], default="waiting", required=True, readonly=True)
    extraction_status = fields.Selection([
        ('need_extraction', 'Extracting information'),
        ('extraction_success', 'Extracting completed.'),
        ('extraction_failed', 'Extraction failed')
    ], default='need_extration', readonly=True)
    #worker_id = fields.Many2one()

    # Extracted Information.
    title = fields.Char(readonly=True,)
    artist = fields.Char(readonly=True,)
    duration = fields.Float(readonly=True,)
    thumbnail_url = fields.Char(
        default="https://via.placeholder.com/320x180/1C1B1F/FFFFFF?text=No+Thumbnail"
    )
    lyric = fields.Text()

    # Karaoke Generated Attributes
    download_url = fields.Char(readonly=True)
    drive_folder_id = fields.Char(readonly=True)
    drive_file_id = fields.Char(readonly=True) # Can be used for preview video

    # Debugging
    error_entries = fields.Json(readonly=True)
    log_entries = fields.Json(readonly=True)
    note = fields.Text('Notes')

    @api.model
    def _cron_extract_info_karaoke(self, batch_size=50):
        """Extract info from source url.

        Extracting concurrently or many many at a times
        can sometimes be a heavy process, since it require network
        and wait time.
        """
        to_extracts = self.search([('extraction_status', '=', 'need_extraction')])
        
        if not to_extracts:
            _logger.debug('No karaoke task to extract, returning...')
            return

        commit_progress = self.env['ir.cron']._commit_progress
        commit_progress(remaining=len(to_extracts))
        
        for karaoke in to_extracts[:batch_size]:
            karaoke = karaoke.try_lock_for_update().filtered(lambda d: d.extraction_status == 'need_extraction')

            if not karaoke:
                continue

            try:
                karaoke._extract_video_info()
                
                _logger.debug(
                    'Karaoke id(%s) information fetched.', karaoke.id
                )

                if karaoke.karaoke_type == "plus":
                    karaoke._extract_lyrics()
                    _logger.debug(
                        'Karaoke id(%s) lyrics fetched.', karaoke.id
                    )

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
                if commit_progress(1):
                    continue
                else:
                    break

    @api.model_create_multi
    def create(self, vals_list):
        """ On Karaoke creation, well use a new threading env.
            To extract necessary information such as title,
            artist, duration, lyrics
        """
        karaokes: KaraokeKaraoke = super().create(vals_list)

        karaokes.extract_info()

        return karaokes

    @api.model
    def get_cookiepath(self):
        #TODO: Rotate cookiefile and populate cookiefile
        return os.path.join(config['data_dir'], "cookies.txt")

    def _flush_logger_hook(self, logger):
        if hasattr(logger, 'task_log_buffer') and logger.task_log_buffer:
            self.log_entries = merge_log(self.log_entries, logger.task_log_buffer)
            logger.task_log_buffer = []
            # We're commiting instead of rollback from when using cron.
            # Log output should be commited.
            self.env.cr.commit()
            netsvc.reset_logger()
    
    def _make_logger(self):
        """ Will make the current karaoke task logger with implementation of
        logger hook from iantirta.media.
        """
        self.ensure_one()
        logger = logging.getLogger(f"iantirta.karaoke.Task({self.id!s})")
        logger.setLevel(logging.DEBUG)

        if not hasattr(logger, 'add_hook'):
            netsvc.setup_logger('iantirta')

        # Custom logger buffer
        if not hasattr(logger, 'task_log_buffer'):
            print("Log doesnt have task_logger buffer")
            logger.task_log_buffer = []

            def _store_log_entries(record):
                msg = netsvc.formatLogMessage(record)
                logger.task_log_buffer.append(msg)

            logger.add_hook(_store_log_entries)

        return logger

    # Extraction Method
    def _extract_lyrics(self):
        """ Extract One Lyric
        """
        self.ensure_one()

        task_logger = self._make_logger()
        try:
            metadata: LyricMetadata = get_lyric(
                self.title,
                self.artist,
                self.duration,
                logger=task_logger,
            )

        except:
            self._flush_logger_hook(task_logger)
            raise

        self.write({
            'title': metadata.trackName,
            'artist': metadata.artistName,
            "lyric": metadata.plainLyrics
        })

        del metadata

        return self

    def _extract_video_info(self):
        """ Extract One Indo
        """
        self.ensure_one()

        metadata: VideoMetadata = extract_video_info(self.source_url)
        self.write({
            "title": metadata.title,
            "artist": metadata.resolved_artist,
            "duration": metadata.duration,
            "thumbnail_url": metadata.thumbnail,
        })
        del metadata

        return self

    def extract_info(self):
        """ Full Extraction multiple records
        """
        self.write({'extraction_status': 'need_extraction'})

        if cron := self.env.ref('karaoke_iantirta.ir_cron_extract_info_karaoke'):
            cron._trigger()

        _logger.debug('Running extract karaoke cron %s', cron.name)
        return self

    # Api Data Processing
    def _prepare_data_api(self, domain: list[tuple], *, limit: int | None = None) -> list[dict]:
        """ Prepare data for api usage
        """
        karaokes = self.sudo().search(domain, limit=limit)
        return [{
            "id": karaoke.id,
            "title": karaoke.title,
            "artist": karaoke.artist,
            "duration": karaoke.duration,
            "lyric": karaoke.lyric,
            "status": karaoke.status,
            "source": karaoke.source_url,
            "karaoke_type": karaoke.karaoke_type,
        } for karaoke in karaokes]

    def _update_from_dict(self, **data) -> None:
        valid_values = [
            'title',
            'artist',
            'thumbnail',
            "download_url",
            "drive_folder_id",
            "drive_file_id",
            'log_entries',
            "error_entries",
        ]
        if not (karaoke_id := data.pop("id", None)):
            raise UserError(_('Method update_from_dict require karaoke id to be passed'))

        if karaoke := self.sudo().browse(karaoke_id).exists():
            valid_data = {k: v for k, v in data.items() if k in valid_values}
            error_entries = valid_data.pop("error_entries", [])

            if len(error_entries) > 0:
                valid_data['status'] = 'failed'
                valid_data['error_entries'] = merge_log(error_entries, karaoke.error_entries)
            elif valid_data.get('download_url'):
                valid_data['status'] = 'completed'
            else:
                valid_data['status'] = 'failed'

            valid_data['log_entries'] = merge_log(karaoke.log_entries, valid_data['log_entries'])

            karaoke.write(valid_data)

        else:
            raise UserError(_("karaoke id not found in the database"))

    # Action
    def action_refetch_info(self):
        self.extract_info()
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
        self.write({
            "status": "waiting",
            "log_entries": False,
            "error_entries": False,
        })
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
