import base64
import json
import logging
import re
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from sigil.addons.karaoke_iantirta import utils as karaoke_utils

from sigil import _, api, fields, models
from sigil.exceptions import ValidationError

if TYPE_CHECKING:
    from .storage_drive import CloudStorage


_logger = logging.getLogger(__name__)


ANSI_COLOR_CODE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class GPUWorker(models.Model):
    _name = 'gpu.worker'
    _description = 'GPU Worker'

    name = fields.Char(required=True)

    quota_json = fields.Json(
        # compute="_compute_quotas",
        store=True
    )

    def _valid_field_parameter(self, field, name):
        return name == 'required_if_provider' or super()._valid_field_parameter(field, name)

    # Required relational
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

    # State management
    code = fields.Selection(
        string="Provider",
        help="The technical code of this worker provider.",
        selection=[('none', "No Provider Set")],
        default='none',
        required=True,
    )
    state = fields.Selection(
        string="State",
        selection=[('disabled', "Disabled"), ('enabled', "Enabled")],
        default='disabled', required=True, copy=False
    )

    # Logging and debug
    run_state = fields.Selection([
        ('starting_up', 'Starting Up'),
        ("ready", "Ready"),
        ("running", "Running"),
        ("error", "Error"),
    ], default="ready", readonly=True, copy=False)
    last_heartbeat = fields.Datetime("Last Heartbeat", readonly=True, copy=False)
    log_entry_ids = fields.One2many(
        comodel_name='gpu.worker.log',
        inverse_name='worker_id',
        copy=False,
    )
    karaoke_ids = fields.One2many(
        comodel_name='karaoke.karaoke',
        inverse_name='worker_id',
        copy=False
    )

    def post_vacuum(self):
        """To be filled for provider that need post vacuum function."""

    @api.model
    def _cron_auto_vacuum_workers(self):
        """
        Scheduled action to run every 5-10 minutes. 
        Detects workers that haven't sent a heartbeat in over 30 minutes.
        """
        timeout_threshold = fields.Datetime.now() - timedelta(minutes=30)

        # Find workers marked as running or starting up that have timed out
        dead_workers = self.search([
            ('run_state', 'in', ['running', 'starting_up']),
            '|',
            ('last_heartbeat', '<', timeout_threshold),
            ('last_heartbeat', '=', False)
        ])

        if dead_workers:
            commit_progress = self.env['ir.cron']._commit_progress
            commit_progress(remaining=len(dead_workers))

            dead_workers.write({'run_state': 'error'})

            abandoned_tasks = self.env['karaoke.karaoke'].search([
                ('status', '=', 'processing'),
                ('worker_id', 'in', dead_workers.ids)
            ])
            if abandoned_tasks:
                abandoned_tasks.write({
                    'status': 'waiting',
                    'worker_id': False
                })

            commit_progress(len(dead_workers))
            _logger.warning("Auto-vacuumed %s dead GPU workers and reset %s abandoned tasks.", len(dead_workers), len(abandoned_tasks))
            dead_workers.post_vacuum()

    def _mark_heartbeat(self):
        """Called by the controller to update the worker's active status."""
        self.ensure_one()
        now = fields.Datetime.now()

        needs_status_change = (self.run_state == 'starting_up')
        is_stale = not self.last_heartbeat or (now - self.last_heartbeat).total_seconds() > 30
        # Avoid serialization error
        if is_stale or needs_status_change:
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

    # @api.depends('name', "code")
    # def _compute_quotas(self):
    #     for record in self:
    #         if record.access_token:
    #             try:
    #                 record.get_quotas()
    #             except Exception as e:
    #                 _logger.error("Failed to fetch quotas for %s: %s", record.name, e)
    #                 record.quota_json = {
    #                     "error": "Failed to fetch quotas",
    #                     "error_str": str(e),
    #                 }
    #         else:
    #             record.quota_json = {}

    def _get_code(self):
        """ Return the code of the provider.

        Note: `self.ensure_one()`

        :return: The code of the provider.
        :rtype: str
        """
        self.ensure_one()
        return self.code

    def _check_required_if_provider(self):
        """ Check that provider-specific required fields have been filled.

        The fields that have the `required_if_provider='<provider_code>'` attribute are made
        required for all `google` records with the `code` field equal to `<provider_code>`
        and with the `state` field equal to `'enabled'` or `'test'`.

        Provider-specific views should make the form fields required under the same conditions.

        :return: None
        :raise ValidationError: If a provider-specific required field is empty.
        """
        field_names = []
        enabled_records = self.filtered(lambda p: p.state == 'enabled')
        for field_name, field in self._fields.items():
            required_for_provider_code = getattr(field, 'required_if_provider', None)
            if required_for_provider_code and any(
                required_for_provider_code == record._get_code() and not record[field_name]
                for record in enabled_records
            ):
                ir_field = self.env['ir.model.fields']._get(self._name, field_name)
                field_names.append(ir_field.field_description)
        if field_names:
            raise ValidationError(
                _("The following fields must be filled: %s", ", ".join(field_names))
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_required_if_provider()

        return records

    def write(self, vals):
        result = super().write(vals)
        self._check_required_if_provider()

        return result

    # Abstract child method
    def get_worker_name(self) -> str:
        return f'gpu_worker:{self.id}'

    def get_worker(self):
        raise NotImplementedError()

    def _prepare_storage_params(self) -> list[str]:
        self.storage_id: CloudStorage
        return [
            f'STORAGE_OPTIONS: dict = {self.storage_id._prepare_notebook_params()}\n'
        ]

    def _prepare_cookie_params(self) -> list[str]:
        # Default cookie path
        from iantirta.media import constants
        default_cookiepath = constants.DEFAULT_NOROTATE_COOKIEPATH
        cookie_content = default_cookiepath.read_text(encoding='utf-8')
        b64_payload = base64.b64encode(cookie_content.encode('utf-8')).decode('utf-8')
        return [
            'import base64\n',
            'from pathlib import Path\n',
            'WORKER_COOKIEPATH = Path("~/.cache/iantirta/cookies.txt").expanduser().resolve()\n',
            'WORKER_COOKIEPATH.parent.mkdir(parents=True, exist_ok=True)\n',
            f'WORKER_COOKIEPATH.write_bytes(base64.b64decode("{b64_payload}"))\n',
        ]

    def _prepare_env_params(self) -> list[str]:
        new_access_token = karaoke_utils.generate_access_token(
            self.name, self.code
        )
        return [
            "# Do Not Modified. Generated by iantirta.com\n",
            "\n",
            f'IANTIRTA_URL = "{self.get_base_url()}"\n',
            f'IANTIRTA_API_KEY = "{new_access_token}"\n',
            f'WORKER_ID = {self.id}\n',
            '\n',
            '# STORAGE PARAMETERS\n',
            *self._prepare_storage_params(),
            "\n",
            *self._prepare_cookie_params(),
            "\n",
            '\n',
            "import os\n",
            'os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"\n',
            'os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"\n',
        ]

    def _prepare_notebook(self) -> dict:
        notebook: dict = self.notebook_id.to_metadata_dict()
        notebook_param: dict = {
            "cell_type": "code",
            "execution_count": None,
            "id": str(uuid.uuid4())[:8],
            "metadata": {},
            "outputs": [],
            "source": self._prepare_env_params(),
        }
        notebook["cells"].insert(0, notebook_param)

        return notebook

    def _prepare_folder(tmpdir: str, tmp_script_path: Path):
        raise NotImplementedError()

    def action_run(self):
        self.ensure_one()

        notebook = self._prepare_notebook()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_script_path = Path(tmpdir) / "worker.ipynb"

            with open(str(tmp_script_path), "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=1)

            folder = self._prepare_folder(tmpdir, tmp_script_path)

            self.run_state = 'starting_up'
            self.get_worker().run(str(folder))

    def get_quotas(self) -> dict:
        self.ensure_one()
        quotas = self.get_worker().get_quota()
        self.quota_json = quotas
        return quotas

    def action_get_quotas(self):
        self.get_quotas()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': _('Successfully refresh quota information.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def update_log_entries(self, log_entries: list[dict]) -> None:
        self.ensure_one()
        if getattr(self, 'log_entries', False,):
            self.log_entries = False

        for log in log_entries:
            log['worker_id'] = self.id
            log['type'] = 'client'
            log['dbname'] = self.env.cr.dbname
            log['level'] = ANSI_COLOR_CODE_RE.sub('', log['level']).strip()
        
        return self.env['gpu.worker.log'].create(log_entries)
