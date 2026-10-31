import base64
import logging
from pathlib import Path

from sigil import SUPERUSER_ID, api, fields, models
from sigil.modules.registry import Registry

_logger = logging.getLogger(__name__)


_DEFAULT_COLAB_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/colaboratory",
    "https://www.googleapis.com/auth/drive.file",
]


class GPUWorker(models.Model):
    _inherit = 'gpu.worker'

    code = fields.Selection(selection_add=[
        ('colab', 'Google Colab')
    ])

    google_client_secrets = fields.Binary(
        string="Google Client OAuth Credentials as .json",
        store=False,
    )
    google_client_secrets_json = fields.Char(
        string="Google Client Secrets",
        compute="_compute_google_client_secrets_json",
        readonly=False,
        store=True,
    )

    # -----------------------
    # Compute method
    # -----------------------

    @api.onchange('google_client_secrets')
    def _compute_google_client_secrets_json(self):
        for record in self:
            if record.code == 'colab':
                creds = record.with_context(
                    bin_size=False
                ).google_client_secrets

                record.google_client_secrets_json = (
                    base64.b64decode(creds)
                    if creds else False
                )

    # -----------------------
    # User Action
    # -----------------------

    def action_setup_user_token(self):
        """
        Setup user token for google oauth api.
        """
        self.ensure_one()
        from ..utils.google_utils import setup_user_token
        return setup_user_token(
            self,
            creds_field='access_token',
            client_config_field='google_client_secrets_json',
            scopes=_DEFAULT_COLAB_SCOPES,
        )

    # Override

    # -----------------------
    # Abstraction method
    # -----------------------

    def get_worker(self):
        if self.code != 'colab':
            return super().get_worker()

        try:
            from iantirta.media import ColabWorker
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Cannot Continue as iantirta-media is not installed"
            )

        return ColabWorker(
            access_token=self.access_token,
            name=f'{self.code}-worker-{self.id}'
        )

    def _process_quota_json(self) -> None:
        """
        Process record quota json into
        ``quota_refresh_time``, ``quota_allowed``, and
        ``quota_used``.

        It could also be used for any necessary checker when
        ``quota_json`` is fetched.

        Since different provider api will give different response.

        Colab is returning a response for usage only available when
        instance/runtime is running, thus we are continuing this on
        ``worker_run`` method for ``allowed`` field
        """
        if self.code != 'colab':
            return super()._process_quota_json()

        self.ensure_one()

        if not self.quota_json:
            return

        quota = self.quota_json

        # Check unsynchronized run state.
        if (
            quota.get('assignmentsCount') == 0
            and self.run_state == 'running'
        ):
            self.run_state = 'error'

        # Process
        if freeQuota := quota.get('freeCcuQuotaInfo'):
            self.quota_used = (
                self.quota_allowed - freeQuota.get('remainingTokens')
                if self.quota_allowed > 0
                else 0
            )
            self.quota_refresh_time = freeQuota.get('nextRefillTimestampSec')

    # -----------------------
    # Worker run helper and abstraction method
    # -----------------------

    def _prepare_script(self, tmpdir: str, worker_instance) -> tuple[Path, dict]:
        """
        Prepare actual script path that would later be
        sent to the worker instance to run.

        Colab expected a file directly

        :param str tmpdir:
        :return: tuple of script path, and run parameters.
        :rtype: tuple[Path, dict]
        """
        if self.code != 'colab':
            return super()._prepare_script(tmpdir, worker_instance)

        tmp_script_path = Path(tmpdir) / "worker_job.py"

        env_lines: list[str] = self._prepare_env_source_code()
        code_lines: list[str] = self.notebook_id.to_source_code()
        source_code = "".join(env_lines + code_lines)

        tmp_script_path.write_text(source_code, encoding='utf-8')

        dbname = self.env.cr.dbname
        _context = self.env.context
        worker_id = self.id

        def on_close():
            """
            Called when disconnected or close
            """
            # Update quota json
            quotas = None

            try:
                quotas = worker_instance.get_quota()
            except Exception as e:
                _logger.exception(
                    "Failed to refresh quota after Colab worker shutdown."
                )

            with Registry(dbname).cursor() as new_cr:
                env = api.Environment(new_cr, SUPERUSER_ID, _context)

                if record := env['gpu.worker'].browse(worker_id).exists():

                    # We change the state to ready
                    # because we are not sure wether its
                    # colab exhausted session or different connection issues.
                    vals = {'run_state': 'ready'}
                    if quotas:
                        vals['quota_json'] = quotas

                    record.write(vals)
                    record.clear_abandoned_tasks()

                    new_cr.commit()

                    _logger.warning("GPU Worker %s closed.", worker_id)

        return tmp_script_path, {
            'run_in_background': True,
            'gpu': True,
            'on_close_hook': on_close,
        }

    def _on_post_worker_run(self, worker_instance):
        """
        Hook called after successfully run worker.

        Continuation for ``allowed`` field that colab api
        response only gives once the runtime is running.
        """
        if self.code != 'colab':
            return super()._on_post_worker_run(worker_instance)

        self.ensure_one()

        quota = None
        try:
            quota = worker_instance.state.client.get_consumption_user_info()

        except Exception as e:
            _logger.warning(f"Error while getting consumtion info, Error: {e}")

        if quota and (freeQuota := quota.freeCcuQuotaInfo):
            self.write({
                'quota_allowed': freeQuota.remainingTokens,
                'quota_refresh_time': freeQuota.nextRefillTimestampSec,
            })
