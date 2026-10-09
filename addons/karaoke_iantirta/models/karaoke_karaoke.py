import json
import os
import threading
import traceback

from sigil import _, api, fields, models
from sigil.modules.registry import Registry
from sigil.tools import config

from .kplus_tools import extract_info, extract_lyrics


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

    # Auto Generated
    title = fields.Char(readonly=True,)
    artist = fields.Char(readonly=True,)
    duration = fields.Float(readonly=True,)
    thumbnail_url = fields.Char(
        default="https://via.placeholder.com/320x180/1C1B1F/FFFFFF?text=No+Thumbnail"
    )

    lyrics = fields.Text()

    # Karaoke Attributes
    download_url = fields.Char(readonly=True)
    drive_folder_id = fields.Char(readonly=True)
    drive_file_id = fields.Char(readonly=True) # Can be used for preview video
    error = fields.Text(readonly=True)
    log = fields.Text(readonly=True)


    @api.model_create_multi
    def create(self, vals_list):
        """ On Karaoke creation, well use a new threading env.
            To extract necessary information such as title,
            artist, duration, lyrics
        """
        all_karaokes = set(
            self.sudo().search([]).mapped("source_url")
        )

        duplicated, missing = set(), set()

        for val in vals_list:
            if val.get("source_url") in all_karaokes:
                duplicated.add(val)
            else:
                missing.add(val)
        karaokes: KaraokeKaraoke = super().create(missing)

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
        lyrics = extract_lyrics(self.title, self.artist, self.duration)
        self.write({"lyrics": lyrics})
        return self

    def _extract_info(self):
        """ Extract One
        """
        self.ensure_one()
        title, artist, duration, thumbnail_url = extract_info(
            self.source_url,
            cookiefile=self.get_cookiepath(),
            return_thumbnail=True,
        )
        self.write({
            "title": title,
            "artist": artist,
            "duration": duration,
            "thumbnail_url": thumbnail_url,
        })
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
    def _prepare_data_api(self, domain: list, *, limit: int | None = None) -> list[dict]:
        """ Prepare data for api usage
        """
        karaokes = self.sudo().search(domain, limit=limit)
        return [{
            "id": karaoke.id,
            "title": karaoke.title,
            "artist": karaoke.artist,
            "duration": karaoke.duration,
            "lyrics": karaoke.lyrics,
            "status": karaoke.status,
            "url": karaoke.source_url,
            "karaoke_type": karaoke.karaoke_type,
        } for karaoke in karaokes]


    def _update_from_list(self, datas: list[dict]) -> None:
        valid_values = [
            "download_url",
            "drive_folder_id",
            "drive_file_id",
            "error",
        ]
        for data in datas:
            if not (karaoke_id := data.pop("id", None)):
                continue

            if karaoke := self.sudo().browse(karaoke_id).exists():
                valid_data = {k: v for k, v in data.items() if k in valid_values}
                error = valid_data.pop("error", {})

                # Determine status: Completed if there is no error OR if a download_url was generated
                if not error or valid_data.get("download_url"):
                    valid_data["status"] = "completed"
                else:
                    valid_data["status"] = "failed"
                
                # We need to json.dumps() for frontend JSON.parse
                valid_data["error"] = json.dumps(error)

                karaoke.write(valid_data)


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
