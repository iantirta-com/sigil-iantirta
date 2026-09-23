import logging
import typing as t

from sigil.addons.karaoke_iantirta import utils as karaoke_utils
from werkzeug.exceptions import BadRequest, Forbidden

from sigil import _
from sigil.exceptions import AccessError, MissingError, ValidationError
from sigil.http import Controller, request, route

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke

_logger = logging.getLogger(__name__)

class KaraokeController(Controller):
    @route("/karaoke/task", type="jsonrpc", auth="public")
    def karaoke_task(
        self,
        worker_name: str,
        worker_provider: str,
        access_token: str,
        status_to_fetch: str,
        **kwargs
    ) -> list:
        """ Get a list of task according to the status needed.
            and generate access token in case needed.
        """
        if not karaoke_utils.check_access_token(
            access_token, worker_name, worker_provider
        ):
            raise Forbidden()

        tasks: KaraokeKaraoke = request.env["karaoke.karaoke"].sudo().search([
            ("status", "=", status_to_fetch)
        ])
        response = []
        for task in tasks:
            response.append({
                "id": task.id,
                "title": task.title,
                "artist": task.artist,
                "duration": task.duration,
                "lyrics": task.lyrics,
                "status": task.status,
                "url": task.source_url,
                "karaoke_type": task.karaoke_type,
            })
        return response

    @route("/karaoke/task/update", type="jsonrpc", auth="public")
    def karaoke_task_update(
        self,
        worker_name: str,
        worker_provider: str,
        access_token: str,
        datas: list[dict],
    ) -> bool:
        if not karaoke_utils.check_access_token(
            access_token, worker_name, worker_provider
        ):
            raise Forbidden()

        karaoke_sudo = request.env["karaoke.karaoke"].sudo()

        for data in datas:
            if karaoke := karaoke_sudo.browse(data.get("id")):
                karaoke.write({
                    "status": data["status"],
                    "download_url": data["download_url"],
                    "drive_folder_id": data["drive_folder_id"],
                    "drive_file_id": data["drive_file_id"],
                    "error": data["error"],
                    "log": data["log"],
                })
            else:
                _logger.warning(f"Karaoke of ID: {data.get('id')} doesn't exists in the database, skiping...")
        return True

    @route("/karaoke/worker/update", type="jsonrpc", auth="public")
    def karaoke_worker(
        self,
        worker_name: str,
        worker_provider: str,
        access_token: str,
        karaoke_ids,
    ) -> bool:
        """ Endpoint for first time running
            it would update status of each the karaoke_ids,
            to be processing.
        """
        worker_sudo = request.env["gpu.worker"].sudo().search([
            ("name", "=", worker_name), ("provider", "=", worker_provider)
        ]).exists()

        if not worker_sudo:
            raise ValidationError(_("The provided parameters are invalid."))
        
        if not karaoke_utils.check_access_token(
            access_token, worker_sudo.name, worker_sudo.provider
        ):
            raise Forbidden()

        karaokes = request.env["karaoke.karaoke"].browse(karaoke_ids).exists()
        if karaokes:
            karaokes.sudo().write({"status": "processing"})
            return True
        else:
            return False

    # Cookiefile