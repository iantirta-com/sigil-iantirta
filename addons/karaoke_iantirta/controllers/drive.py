import typing as t

from werkzeug.exceptions import BadRequest, Forbidden

from sigil.http import Controller, request, route

from sigil.addons.karaoke_iantirta import utils as karaoke_utils

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke


class DriveController(Controller):
    @route("/google_drive/callback", type="http", auth="user")
    def drive_callback(self, error: str | None = None, **kwargs):
        if error:
            return request.make_response(f"Authentication failed: {error}")

        try:
            from ..models import drive_tools
        except ImportError:
            raise ImportError("Cannot Continue as google-auth is not installed")
        
        code = kwargs.pop("code")
        worker_id = kwargs.pop("state")
        
        if not code or not worker_id:
            return request.make_response("Invalid request. Missing code or state.")

        worker = request.env['gpu.worker'].browse(int(worker_id))
        if not worker.exists():
            return request.make_response("GPU Worker record not found.")

        creds = drive_tools.post_create_creds(code)
        worker.gdrive_access_token_json = creds.to_json()
        return request.redirect(f'/web#id={worker.id}&model=gpu.worker&view_type=form')
