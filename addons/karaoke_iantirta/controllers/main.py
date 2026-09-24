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
            return karaoke_sudo._prepare_data_api(domain, limit=limit)
        elif action == "update":
            tasks_list: list[dict] = kwargs.pop("tasks", [])
            karaoke_sudo._update_from_list(tasks_list)
            return True
        elif action == "events":
            # Separate Worker event and karaoke event
            events = kwargs.pop("events", [])

            grouped = {}
            for event in events:
                grouped.setdefault(event.get("task_id"), []).append(event)

            def combine_log(current_str: str, extra) -> str:
                if not current_str or not isinstance(current_str, str) or not current_str.strip():
                    parsed_current = []
                else:
                    try:
                        parsed_current = json.loads(current_str)
                    except json.JSONDecodeError:
                        try:
                            parsed_current = ast.literal_eval(current_str)
                            if not isinstance(parsed_current, list):
                                parsed_current = []
                        except (ValueError, SyntaxError):
                            parsed_current = []
                return json.dumps(parsed_current + extra)

            for task_id, event in grouped.items():
                if task_id is None:
                    # This event belong to worker
                    worker_sudo.log = combine_log(worker_sudo.log, event)
                elif karaoke := karaoke_sudo.browse(task_id).exists():
                    karaoke.log = combine_log(karaoke.log, event)

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