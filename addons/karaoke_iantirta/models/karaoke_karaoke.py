import os
import threading

from sigil import _, api, fields, models
from sigil.tools import config
from sigil.modules.registry import Registry

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
    error = fields.Json(readonly=True)
    log = fields.Text(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)

        def extract_info_with_new_cursor():
            with Registry(self.env.cr.dbname).cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                for task in env["karaoke.karaoke"].browse(tasks.ids):
                    task.extract_info()

        @self.env.cr.postcommit.add
        def launch_thread():
            thread = threading.Thread(target=extract_info_with_new_cursor)
            thread.daemon = True  # Allows the server to shut down without getting stuck
            thread.start()

        return tasks

    @api.model
    def get_cookiepath(self):
        #TODO: Rotate cookiefile and populate cookiefile
        return os.path.join(config['data_dir'], "cookies.txt")
        
    def extract_info(self) -> None:
        self.ensure_one()
        try:
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
            if self.karaoke_type == "plus":
                self.write({
                    "lyrics": extract_lyrics(self.title, self.artist, self.duration)
                })
        except Exception as err:
            self.write({
                "error": f"Extract Info: {str(err)}",
            })

    def action_refetch_info(self):
        for rec in self:
            rec.extract_info()
        
        message = _(
            "The Tasks that you selected have been successfully refetched its information."
        )
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
        self.write({"status": "waiting"})
        message = _(
            "The Tass that you selected have been successfully resetted to 'waiting'."
        )
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

    # Task.run() will immediately run
    def action_run(self) -> None:
        """ Run the karaoke task immediately.

            This is intentionally the entry point from the UI.
            The actual processing lives in `_run()`,
            which can later be executed by a GPU worker.
        """
        pass
    # processjobs will be run on scheduled
    