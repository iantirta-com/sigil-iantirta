import json
import os
import threading
import traceback

from sigil import _, api, fields, models
from sigil.exceptions import UserError
from sigil.modules.registry import Registry
from sigil.tools import config

from ..utils import LyricMetadata, VideoMetadata, extract_video_info, get_lyric, merge_log


class KaraokeKaraoke(models.Model):
    _name = 'karaoke.karaoke'
    _description = 'Karaoke Karaoke'
    _rec_name = 'source_url'

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
        ("waiting", "Waiting"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ], default="waiting", required=True, readonly=True)

    #worker_id = fields.Many2one()

    # Auto Generated
    title = fields.Char(readonly=True,)
    artist = fields.Char(readonly=True,)
    duration = fields.Float(readonly=True,)
    thumbnail_url = fields.Char(
        default="https://via.placeholder.com/320x180/1C1B1F/FFFFFF?text=No+Thumbnail"
    )

    lyric = fields.Text()

    # Karaoke Attributes
    download_url = fields.Char(readonly=True)
    drive_folder_id = fields.Char(readonly=True)
    drive_file_id = fields.Char(readonly=True) # Can be used for preview video
    error = fields.Text(readonly=True)
    log = fields.Text(readonly=True)

    error_entries = fields.Json(readonly=True)
    log_entries = fields.Json(readonly=True)


    @api.model_create_multi
    def create(self, vals_list):
        """ On Karaoke creation, well use a new threading env.
            To extract necessary information such as title,
            artist, duration, lyrics
        """
        karaokes: KaraokeKaraoke = super().create(vals_list)

        def extract_info_with_new_cursor():
            with Registry(self.env.cr.dbname).cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)

                karaoke: KaraokeKaraoke
                for karaoke in env["karaoke.karaoke"].browse(karaokes.ids):
                    karaoke.extract_info()

        @self.env.cr.postcommit.add
        def launch_thread() -> None:
            thread = threading.Thread(target=extract_info_with_new_cursor)
            thread.daemon = True  # Allows the server to shut down without getting stuck
            thread.start()

        return karaokes

    @api.model
    def get_cookiepath(self):
        #TODO: Rotate cookiefile and populate cookiefile
        return os.path.join(config['data_dir'], "cookies.txt")

    # Extraction Method
    def _extract_lyrics(self):
        """ Extract One Lyric
        """
        self.ensure_one()

        metadata: LyricMetadata = get_lyric(
            self.title,
            self.artist,
            self.duration
        )
        self.write({
            'title': metadata.trackName,
            'artist': metadata.artistName,
            "lyric": metadata.plainLyrics
        })
        del metadata

        return self

    def _extract_info(self):
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
        for record in self:
            try:
                record._extract_info()
            except Exception as exc:
                error = {
                    "type": str(type(exc)),
                    "message": str(exc),
                    "traceback": "".join(traceback.format_exception(exc)),
                }
                record.error = error
            if record.karaoke_type == "plus":
                try:
                    record._extract_lyrics()
                except Exception as exc:
                    error = {
                        "type": str(type(exc)),
                        "message": str(exc),
                        "traceback": "".join(traceback.format_exception(exc)),
                    }
                    record.error = error

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
                valid_data['error_entries'] = merge_log(karaoke.error_entries, error_entries)
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
        message = _("Successfully refetch info %s task(s).") % len(self)
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
            "log": False,
            "error": False,
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
