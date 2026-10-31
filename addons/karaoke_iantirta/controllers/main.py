# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import logging
from typing import TYPE_CHECKING, Any

from werkzeug.exceptions import Forbidden

from sigil import _
from sigil.exceptions import UserError, ValidationError
from sigil.http import Controller, request, route

from .. import utils as karaoke_utils

if TYPE_CHECKING:
    from ..models.gpu_worker import GPUWorker
    from ..models.karaoke_karaoke import KaraokeKaraoke


_logger = logging.getLogger(__name__)


class KaraokeController(Controller):
    def _check_access(
        self,
        access_token: str,
        worker_id: int,
        **kwargs
    ) -> 'GPUWorker':
        """
        Authenticate request via generated access token.
        given to the worker at the time of running.

        :param str access_token:
        :param int worker_id:
        :return: GPUWorker if the auth successfull.
        :rtype: type[GPUWorker]
        """
        worker_sudo = request.env[
            "gpu.worker"
        ].sudo().browse(worker_id).exists()

        if not worker_sudo:
            raise ValidationError(_("The provided parameters are invalid."))

        if not karaoke_utils.check_access_token(
            access_token, worker_sudo.name, worker_sudo.code
        ):
            raise Forbidden()

        worker_sudo._mark_heartbeat()

        return worker_sudo

    # -----------------------
    # Karaoke endpoint
    # -----------------------

    @route('/karaoke/tasks/get', type='jsonrpc', auth='public')
    def karaoke_tasks_get(
        self,
        limit: int | None = None,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Get karaoke task based on the domain given.
        and will return the prepared data.

        :param int | None limit:
        :return: list dictionary of karaoke data
        :rtype: list[dict[str, Any]]
        """
        self._check_access(**kwargs)

        domain = [
            ('status', '=', 'waiting'),
            ('worker_id', '=', False),
        ]

        # Should implement some kind of lock mechanism.
        return request.env["karaoke.karaoke"].sudo()._prepare_data_api(domain, limit=limit)

    @route('/karaoke/task/update', type='jsonrpc', auth='public')
    def karaoke_task_update(
        self,
        tasks: list[dict] | None = None,
        **kwargs
    ) -> bool:
        """
        Update task with new data specified in ``_update_from_dict``

        :param list[dict[str, Any]] tasks:
        :rtype: bool
        """
        worker_sudo = self._check_access(**kwargs)

        if not tasks:
            raise UserError(_(
                'At least param of `tasks` need to be provided.'
            ))

        karaoke: KaraokeKaraoke
        try:
            for task in tasks:
                if karaoke := request.env["karaoke.karaoke"].sudo().browse(task['id']).exists():

                    if karaoke.worker_id != worker_sudo.id:
                        raise Forbidden()

                    if karaoke.status != 'processing':
                        raise UserError(_(
                            "Task is not being processed by this worker."
                        ))

                    karaoke._update_from_dict(**task)
            return True

        except Exception:
            _logger.exception("Failed to update karaoke tasks")
            raise UserError('Error while updating karaoke model')

    # -----------------------
    # Worker endpoint
    # -----------------------

    @route('/karaoke/worker/claim_task', type='jsonrpc', auth='public')
    def karaoke_worker_claim_task(
        self,
        task_ids: list[int],
        **kwargs,
    ) -> bool:
        """
        Claim tasks to be mark as processing

        :param list[int] task_ids:
        :rtype: bool
        """
        worker_sudo = self._check_access(**kwargs)

        if karaokes := request.env[
            "karaoke.karaoke"
        ].sudo().browse(task_ids).exists():

            if any(karaokes.filtered(lambda k: k.status != 'waiting' or k.worker_id)):
                raise UserError(_("Duplicate processed karaoke tasks."))

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
        """
        Mark worker run state as running

        :rtype: bool
        """
        worker_sudo = self._check_access(**kwargs)

        if worker_sudo.run_state != 'starting_up':
            raise UserError(_("Worker is not starting up."))

        worker_sudo.write({"run_state": "running"})
        return True

    @route('/karaoke/worker/stop', type='jsonrpc', auth='public')
    def karaoke_worker_stop(
        self,
        log_entries: list[dict] | None = None,
        **kwargs,
    ) -> bool:
        """
        Mark worker run state as finished successfully.
        calling this api means that worker completely
        finished the provided notebook, and really shutting down
        normally.

        :param list[dict] | None log_entries:
        :rtype: bool
        """
        worker_sudo = self._check_access(**kwargs)

        # Only processed last 1000 logs
        log_entries = (log_entries or [])[-1000:]

        worker_sudo.clear_abandoned_tasks()

        worker_sudo.write({
            "run_state": "ready",
        })
        worker_sudo.update_log_entries(log_entries)

        return True
