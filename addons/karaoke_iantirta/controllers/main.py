import ast
import json
import logging
import typing as t
from itertools import groupby
from typing import Any, Literal
import warnings

from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from sigil import _
from sigil.exceptions import ValidationError, UserError
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
            access_token, worker_sudo.name, worker_sudo.code
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
        task: dict | None = None,
        tasks: list[dict] | None = None,
        **kwargs
    ) -> bool:
        worker_sudo = self._check_access(**kwargs)

        if not task and not tasks:
            raise UserError(_('At least param of `tasks` need to be provided.'))
        
        if task is not None:
            warnings.warn("Deprecated the `task` parameter should be converted to `task`: list[dict] instead.", DeprecationWarning)
            if tasks:
                tasks = tasks + [task]
            else:
                tasks = [task]

        karaoke: KaraokeKaraoke
        try:
            for _task in tasks:
                if karaoke := request.env["karaoke.karaoke"].sudo().browse(_task['id']).exists():
                    karaoke._update_from_dict(**_task)
            return True
        except Exception as e:
            return UserError(f'Error while updating karaoke model: {e}')

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

        worker_sudo.write({"run_state": "running"})
        return True

    @route('/karaoke/worker/stop', type='jsonrpc', auth='public')
    def karaoke_worker_stop(
        self,
        log_entries: list[dict],
        **kwargs,
    ) -> bool:
        worker_sudo = self._check_access(**kwargs)

        if len(log_entries) > 1000:
            log_entries = log_entries[-1000:]

        abandoned = 0
        for karaoke in worker_sudo.karaoke_ids:
            if karaoke.status == 'processing':
                karaoke.status = 'waiting'
                abandoned += 1
        if abandoned > 0:
            _logger.debug(f"Abandoning karaoke task, count=({abandoned})")

        worker_sudo.write({
            "run_state": "ready",
            'karaoke_ids': False,
        })
        worker_sudo.update_log_entries(log_entries)
        return True
