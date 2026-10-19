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
            from iantirta.media import DriveStorage
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

        storage_id = kwargs.pop('state')

        if not storage_id:
            return request.make_response("Invalid request. Missing Storage ID.")

        storage = request.env['iantirta.cloud.storage'].browse(int(storage_id)).exists()
        
        creds = DriveStorage.get_gdrive_credentials_from_auth_url(
            storage.gdrive_client_config,
            key=f'drive_{storage.id}',
            code=kwargs.pop('code'),
        )

        storage.gdrive_access_token_json = creds.to_json()

        return request.redirect(
            f'/web#id={storage.id}&model=iantirta.cloud.storage&view_type=form'
        )
