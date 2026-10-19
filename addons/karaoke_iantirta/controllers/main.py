import ast
import json
import logging
import typing as t
from itertools import groupby
from typing import Any, Literal

from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from sigil import _
from sigil.exceptions import ValidationError
from sigil.http import Controller, request, route

from .. import utils as karaoke_utils

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke


_logger = logging.getLogger(__name__)


class KaraokeController(Controller):
    def _check_access(
        self,
        access_token: str,
        worker_id: int,
        **kwargs
    ):
        worker_sudo = request.env["gpu.worker"].sudo().browse(worker_id).exists()
        if not worker_sudo:
            raise ValidationError(_("The provided parameters are invalid."))

        if not karaoke_utils.check_access_token(
            access_token, worker_sudo.name, worker_sudo.provider
        ):
            raise Forbidden()

        worker_sudo._mark_heartbeat()

        return worker_sudo

    @route('/karaoke/tasks/get', type='jsonrpc', auth='public')
    def karaoke_tasks_get(
        self,
        domain: list[tuple],
        limit: int | None = None,
        **kwargs
    ) -> list[dict[str, Any]]:
        worker_sudo = self._check_access(**kwargs)

        return request.env["karaoke.karaoke"].sudo()._prepare_data_api(domain, limit=limit)

    @route('/karaoke/task/update', type='jsonrpc', auth='public')
    def karaoke_task_update(
        self,
        task: dict,
        **kwargs
    ) -> bool:
        worker_sudo = self._check_access(**kwargs)
        
        karaoke: KaraokeKaraoke
        if karaoke := request.env["karaoke.karaoke"].sudo().browse(task['id']).exists():
            karaoke._update_from_dict(**task)
            return True
        
        raise NotFound("Karaoke id not found in the database")

    @route('/karaoke/worker/claim_task', type='jsonrpc', auth='public')
    def karaoke_worker_claim_task(
        self,
        task_ids: list[int],
        **kwargs,
    ) -> list[dict[str, Any]]:
        worker_sudo = self._check_access(**kwargs)

        if karaokes := request.env["karaoke.karaoke"].sudo().browse(task_ids).exists():
            karaokes.write({
                "status": "processing",
                'worker_id': worker_sudo.id
            })

        return True

    @route('/karaoke/worker/start', type='jsonrpc', auth='public')
    def karaoke_worker_start(
        self,
        **kwargs,
    ) -> bool:
        worker_sudo = self._check_access(**kwargs)

        worker_sudo.write({"status": "running"})
        return True

    @route('/karaoke/worker/stop', type='jsonrpc', auth='public')
    def karaoke_worker_stop(
        self,
        log_entries: list[str],
        **kwargs,
    ) -> bool:
        worker_sudo = self._check_access(**kwargs)

        worker_sudo.write({
            "status": "ready",
            'log_entries': karaoke_utils.merge_log(
                worker_sudo.log_entries,
                log_entries,
                max_items=1000,
            )
        })
        return True
