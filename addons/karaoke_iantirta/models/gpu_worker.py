# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import base64
import logging
import re
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from sigil.addons.karaoke_iantirta import utils as karaoke_utils

from sigil import _, api, fields, models
from sigil.exceptions import UserError

if TYPE_CHECKING:
    from .storage_drive import CloudStorage


_logger = logging.getLogger(__name__)


ANSI_COLOR_CODE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class GPUWorker(models.Model):
    _name = 'gpu.worker'
    _description = 'GPU Worker'

    name = fields.Char(required=True)

    # Relational
    storage_id = fields.Many2one(
        comodel_name="iantirta.cloud.storage",
        string="Storage",
        required=True
    )
    notebook_id = fields.Many2one(
        comodel_name="worker.notebook",
        string="Notebook",
        required=True
    )
    karaoke_ids = fields.One2many(
        comodel_name='karaoke.karaoke',
        inverse_name='worker_id',
        copy=False
    )

    code = fields.Selection(
        string="Provider",
        selection=[],
        help="The technical code of this worker provider.",
        required=True,
    )

    access_token = fields.Char(
        copy=False,
    )

    # Logging and debug
    run_state = fields.Selection([
        ('starting_up', 'Starting Up'),
        ("ready", "Ready"),
        ("running", "Running"),
        ("error", "Error"),
    ], default="ready", readonly=True, copy=False)
    last_heartbeat = fields.Datetime(
        "Last Heartbeat",
        readonly=True,
        copy=False
    )
    log_entry_ids = fields.One2many(
        comodel_name='gpu.worker.log',
        inverse_name='worker_id',
        copy=False,
    )

    quota_json = fields.Json(
        copy=False,
        store=True
    )
    quota_allowed = fields.Integer(
        'Allowed',
        readonly=True,
        copy=False,
        store=True,
        compute='_compute_quota_refresh_time',
    )
    quota_used = fields.Integer(
        'Used',
        readonly=True,
        copy=False,
        store=True,
        compute='_compute_quota_refresh_time',
    )
    quota_refresh_time = fields.Datetime(
        'Quota Refresh Time',
        readonly=True,
        copy=False,
        store=True,
        compute='_compute_quota_refresh_time'
    )

    is_available = fields.Boolean(
        readonly=True,
        string="Available",
        copy=False,
        store=True,
        compute="_compute_is_available"
    )

    # -----------------------
    # Compute method
    # -----------------------

    @api.depends('run_state', 'quota_json', 'quota_allowed', 'quota_used')
    def _compute_is_available(self):
        for record in self:
            record.is_available = record._is_available()

    @api.depends('quota_json')
    def _compute_quota_refresh_time(self):
        for record in self:
            if record.quota_json:
                record._process_quota_json()

    # -----------------------
    # Cron method
    # -----------------------

    @api.model
    def _cron_auto_vacuum_workers(self):
        """
        Scheduled action to run every 5-10 minutes.

        Detects workers that haven't sent a heartbeat in over 30 minutes.
        """
        timeout_threshold = fields.Datetime.now() - timedelta(minutes=30)

        dead_workers = self.search([
            ('run_state', 'in', ['running', 'starting_up']),
            '|',
            ('last_heartbeat', '<=', timeout_threshold),
            ('last_heartbeat', '=', False)
        ])
        if dead_workers:
            commit_progress = self.env['ir.cron']._commit_progress
            commit_progress(remaining=len(dead_workers))

            dead_workers.write({'run_state': 'error'})
            dead_workers.clear_abandoned_tasks()

            commit_progress(len(dead_workers))

            _logger.warning(
                "Auto-vacuumed %s dead GPU workers..",
                len(dead_workers)
            )

    @api.model
    def _cron_auto_run_workers(self):
        """
        Scheduled action that will run every 5-10 minutes.

        Will check if any pending tasks then will run any
        available worker at disposal.
        """
        if self.env['karaoke.karaoke'].search_count([
            ('status', '=', 'waiting')
        ]) > 0:
            domain = [
                ('run_state', '=', 'ready'),
                ('is_available', '=', True)
            ]
            if available_workers := self.search(domain):
                commit_progress = self.env['ir.cron']._commit_progress
                commit_progress(remaining=len(available_workers))

                for w in available_workers:
                    w = w.try_lock_for_update().filtered_domain(domain)
                    if not w:
                        continue

                    try:
                        # sometimes this would wait for
                        # 10, 20, 40s making 70s wait in total backoff...
                        # thus we'll make max_retries = 1
                        w.worker_run()
                        commit_progress(1, remaining=0)

                        # Only start 1 at a time if success
                        break

                    except Exception as e:
                        _logger.warning(
                            f'Failed to start GPU worker {w.id}. Error: {e}'
                        )

                        w.run_state = 'error'

                        if commit_progress(1):
                            continue
                        else:
                            break

    # -----------------------
    # Abstraction method
    # -----------------------

    def get_worker(self):
        """
        Get worker instance specific for each provider.

        Provider method should override this.
        """

    def _is_available(self) -> bool:
        """
        See if worker is available based on certain conditions.

        Provider method should inherit, add, or override this if needed.
        """
        self.ensure_one()

        return bool(
            self.access_token
            and self.run_state == 'ready'
            and self.quota_json
            and self.quota_used < self.quota_allowed
        )

    def _process_quota_json(self) -> None:
        """
        Process record quota json into
        ``quota_refresh_time``, ``quota_allowed``, and
        ``quota_used``.

        It could also be used for any necessary checker when
        ``quota_json`` is fetched.

        Since different provider api will give different response.

        Provider method should override this.
        """

    # -----------------------
    # Worker run helper and abstraction method
    # -----------------------

    def _prepare_storage_params(self) -> list[str]:
        """
        Prepare necessary storage options that will be pass
        along env source code.

        :return: list of source code python
        :rtype: list[str]
        """
        self.storage_id: CloudStorage
        return [
            '# STORAGE PARAMETERS\n',
            f'STORAGE_OPTIONS: dict = {self.storage_id._prepare_notebook_params()}\n'
        ]

    def _prepare_cookie_params(self) -> list[str]:
        """
        Prepared necessary cookies parameters that will be passed
        along env source code, used by ytdlp for worker instance.
        
        :return: list of source code python
        :rtype: list[str]
        """
        from iantirta.media import constants

        # Default cookie path
        default_cookiepath = constants.DEFAULT_NOROTATE_COOKIEPATH

        cookie_content = base64.b64encode(
            default_cookiepath.read_bytes()
        ).decode('utf-8')

        return [
            '# COOKIES PARAMETERS\n',
            'import base64\n',
            'from pathlib import Path\n',
            'WORKER_COOKIEPATH = Path("~/.cache/iantirta/cookies.txt").expanduser().resolve()\n',
            'WORKER_COOKIEPATH.parent.mkdir(parents=True, exist_ok=True)\n',
            f'WORKER_COOKIEPATH.write_bytes(base64.b64decode("{cookie_content}"))\n',
        ]

    def _prepare_env_source_code(self) -> list[str]:
        """
        Prepared env source code to be given along
        with the notebook script source code.

        :return: list of source code python
        :rtype: list[str]
        """
        self.ensure_one()

        worker_access_token = karaoke_utils.generate_access_token(
            self.name, self.code
        )

        return [
            "# Do Not Modified. Generated by iantirta.com\n",
            "\n",
            f'IANTIRTA_URL = "{self.get_base_url()}"\n',
            f'IANTIRTA_API_KEY = "{worker_access_token}"\n',
            f'WORKER_ID = {self.id}\n',
            '\n',
            *self._prepare_storage_params(),
            "\n",
            *self._prepare_cookie_params(),
            "\n",
            '# transformers and huggingface env.\n',
            "import os\n",
            'os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"\n',
            'os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"\n',
        ]

    def _prepare_script(self, tmpdir: str, worker_instance) -> tuple[Path, dict]:
        """
        Prepare actual script path that would later be
        sent to the worker instance to run.

        Provider method should override this.

        :param str tmpdir:
        :return: tuple of script path, and run parameters.
        :rtype: tuple[Path, dict]
        """

    def _on_post_worker_run(self, worker_instance):
        """
        Hook called after successfully run worker.

        Provider method should override this if needed.
        """
        self.ensure_one()

        self.get_quotas(worker_instance)

    def _handle_worker_run_error(self, e: Exception):
        """
        Handle worker run error.

        :param Exception e:
        """
        raise e

    # -----------------------
    # Actionable Method
    # -----------------------

    def _mark_heartbeat(self):
        """
        Called by the controller to update
        the worker's active status.
        """
        self.ensure_one()

        now = fields.Datetime.now()

        # Avoid serialization error
        if (
            self.run_state == 'starting_up'
            or not self.last_heartbeat
            or (now - self.last_heartbeat).total_seconds() > 30
        ):
            self.env.cr.execute("""
                UPDATE gpu_worker SET last_heartbeat=%(now)s
                WHERE id IN (
                    SELECT id FROM gpu_worker WHERE id = %(worker_id)s
                    FOR NO KEY UPDATE SKIP LOCKED
                )
            """, {
                'now': now,
                'worker_id': self.id,
            })

    def update_log_entries(self, log_entries: list[dict]) -> None:
        """
        Method that will update current worker log entries.

        This will probably filling up so much database records.

        :param list[dict] log_entries:
        """
        self.ensure_one()

        for log in log_entries:
            log['worker_id'] = self.id
            log['type'] = 'client'
            log['dbname'] = self.env.cr.dbname
            log['level'] = ANSI_COLOR_CODE_RE.sub('', log['level']).strip()

        return self.env['gpu.worker.log'].create(log_entries)

    def clear_abandoned_tasks(self) -> None:
        """
        Method that will clear any abandoned tasks.

        abandoned tasks is task where ``status`` == ``processing``
        and belong to this worker ids.
        """
        abandoned_tasks = self.env['karaoke.karaoke'].search([
            ('status', '=', 'processing'),
            ('worker_id', 'in', self.ids)
        ])

        # This will automatically clear
        # relational fields for this worker
        if abandoned_tasks:
            abandoned_tasks.write({
                'status': 'waiting',
                'worker_id': False
            })

        _logger.warning(
            "Resetting %s abandoned tasks.",
            len(abandoned_tasks)
        )

    def get_quotas(self, worker_instance=None) -> dict:
        """
        Method that will be passed to the worker instance.
        Will update ``quota_json`` in the meantime.

        :return: dictionary data of any provider given.
        :rtype: dict[str, Any]
        """
        self.ensure_one()

        if not worker_instance:
            worker_instance = self.get_worker()

        quotas: dict = worker_instance.get_quota()
        self.quota_json = quotas

        return quotas

    def worker_run(self):
        """Actually Run worker"""
        self.ensure_one()

        worker_instance = self.get_worker()

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path, run_params = self._prepare_script(tmpdir, worker_instance)

            try:
                # Preserve in case failed
                original_status = self.run_state
                self.run_state = 'starting_up'

                worker_instance.run(
                    script_path.as_posix(),
                    **run_params
                )

                self._on_post_worker_run(worker_instance)
                self.last_heartbeat = fields.Datetime.now()

            except Exception as e:
                self._handle_worker_run_error(e)
                self.run_state = original_status

    # -----------------------
    # User Action
    # -----------------------

    def action_get_quotas(self):
        if not self.access_token:
            raise UserError(_("Access token is needed to fetch worker quota"))
        self.get_quotas()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': _('Successfully refresh quota information.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'soft_reload'
                },
            }
        }

    def action_run(self):
        """
        Run worker.
        """
        if not self.access_token:
            raise UserError(_("Access token is needed to run worker"))
        params = {
            'message': _('Successfully Run worker.'),
            'type': 'success',
            'sticky': False,
            'next': {
                'type': 'ir.actions.client',
                'tag': 'soft_reload'
            },
        }
        try:
            self.worker_run()
        except Exception:
            params.update({
                'message': _("Failed to run worker"),
                'type': 'danger',
            })
   
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': params
        }
