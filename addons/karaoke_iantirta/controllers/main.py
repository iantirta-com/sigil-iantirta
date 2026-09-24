import ast
import json
import logging
import typing as t
from itertools import groupby

from sigil.addons.karaoke_iantirta import utils as karaoke_utils
from werkzeug.exceptions import BadRequest, Forbidden

from sigil import _
from sigil.exceptions import AccessError, MissingError, ValidationError
from sigil.http import Controller, request, route

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke

_logger = logging.getLogger(__name__)

class KaraokeController(Controller):
    def _check_access(self, access_token: str, worker_id: int, **kwargs):
        worker_sudo = request.env["gpu.worker"].sudo().browse(worker_id).exists()
        if not worker_sudo:
            raise ValidationError(_("The provided parameters are invalid."))

        if not karaoke_utils.check_access_token(
            access_token, worker_sudo.name, worker_sudo.provider
        ):
            raise Forbidden()

        return worker_sudo

    @route("/karaoke/tasks", type="jsonrpc", auth="public")
    def karaoke_tasks(
        self,
        action: t.Literal["get", "update", "events"],
        **kwargs
    ) -> list | bool:
        worker_sudo = self._check_access(**kwargs)

        karaoke_sudo: KaraokeKaraoke = request.env["karaoke.karaoke"].sudo()

        if action == "get":
            domain = kwargs.pop("domain", [])
            limit = kwargs.pop("limit", None)
            tasks = karaoke_sudo.search(domain, limit=limit)
            return [
                {
                    "id": task.id,
                    "title": task.title,
                    "artist": task.artist,
                    "duration": task.duration,
                    "lyrics": task.lyrics,
                    "status": task.status,
                    "url": task.source_url,
                    "karaoke_type": task.karaoke_type,
                }
                for task in tasks
            ]
        elif action == "update":
            tasks_list: list[dict] = kwargs.pop("tasks", [])
            for task in tasks_list:
                task_id = task.pop("id")
                if karaoke := karaoke_sudo.browse(task_id).exists():
                    error = task.pop("error", {})
                    print(error)
                    if not error:
                        task["status"] = "completed"
                    else:
                        task["status"] = "failed"
                    task["error"] = json.dumps(error)
                    print(task["status"])
                    karaoke.write(task)
                else:
                    _logger.warning(
                        f"Karaoke of ID: {task_id} "
                        "doesn't exists in the database, skiping..."
                    )
            return True
        elif action == "events":
            # Separate Worker event and karaoke event
            events = kwargs.pop("events", [])
            grouped_events = {}
            for event in events:
                grouped_events.setdefault(event.get("task_id"), []).append(event)
            for task_id, log in grouped_events.items():
                if task_id is not None and (karaoke := karaoke_sudo.browse(task_id).exists()):
                    current_log = json.loads(karaoke.log) if karaoke.log and karaoke.log.strip() else []
                    full_log = current_log + log
                    karaoke.write({"log": json.dumps(full_log)})
                elif task_id is None:
                    current_log = json.loads(worker_sudo.log) if worker_sudo.log and worker_sudo.log.strip() else []
                    full_log = current_log + log
                    worker_sudo.write({"log": json.dumps(full_log)})
                else:
                    _logger.warning(f"Karaoke with {task_id} not found.")
            return True
        else:
            raise ValidationError(_("Action isn't supported"))
        
    @route("/karaoke/worker", type="jsonrpc", auth="public")
    def karaoke_worker(
        self,
        action: t.Literal["start", "stop",],
        **kwargs
    ) -> list | bool:
        worker_sudo = self._check_access(**kwargs)

        if action == "start":
            task_ids = kwargs.pop("task_ids", [])
            if karaokes := request.env["karaoke.karaoke"].sudo().browse(task_ids).exists():
                karaokes.write({"status": "processing"})
            worker_sudo.write({"status": "running"})
            return True
        elif action == "stop":
            worker_sudo.write({"status": "ready"})
            return True
        else:
            raise ValidationError(_("Action isn't supported"))

    # Cookiefile