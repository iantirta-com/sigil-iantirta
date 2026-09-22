import typing as t

from werkzeug.exceptions import BadRequest, Forbidden

from sigil.http import Controller, request, route

from sigil.addons.karaoke_iantirta import utils as karaoke_utils

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke


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

        for data in datas:
            if karaoke := request.env["karaoke.karaoke"].browse(data.pop("id")):
                karaoke.write({
                    "status": data["status"],
                    "download_url": data["download_url"],
                    "drive_folder_id": data["drive_folder_id"],
                    "drive_file_id": data["drive_file_id"],
                    "error": data["error"],
                    "log": data["log"],
                })
        return True

    @route("/karaoke/worker/update", type="jsonrpc", auth="public")
    def karaoke_worker(
        self,
        worker_name: str,
        worker_provider: str,
        access_token: str,
        karaoke_ids,
    ) -> None:
        """ Endpoint for first time running
            it would update status of each the karaoke_ids,
            to be processing.
        """
        if not karaoke_utils.check_access_token(
            access_token, worker_name, worker_provider
        ):
            raise Forbidden()

        karaokes = request.env["karaoke.karaoke"].browse(karaoke_ids)
        karaokes.write({"status": "processing"})

    # Cookiefile