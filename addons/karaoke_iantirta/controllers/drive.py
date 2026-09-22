import typing as t

from werkzeug.exceptions import BadRequest, Forbidden

from sigil.http import Controller, request, route

from sigil.addons.karaoke_iantirta import utils as karaoke_utils

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke


class DriveController(Controller):
    @route("/google_drive/callback", type="http", auth="user")
    def drive_callback(self, **kwargs):
        print("CallBack", kwargs)