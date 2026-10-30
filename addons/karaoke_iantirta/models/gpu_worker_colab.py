import base64
import logging
import tempfile
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
    ], ondelete={'colab': 'set default'})

    google_client_secrets = fields.Binary(
        string="Google Client OAuth Credentials as .json",
        store=False,
        copy=False,
    )
    google_client_secrets_json = fields.Char(
        string="Google Client Secrets",
        compute="_compute_google_client_secrets_json",
        readonly=False,
        store=True,
        required_if_provider='colab',
        copy=False,
    )
    google_user_token_json = fields.Char(
        copy=False,
    )

    initial_token = fields.Integer(
        string='Initial Free CCU Tokens',
        readonly=True,
        copy=False,
    )
    remaining_tokens = fields.Integer(
        string='Remaining Free CCU Tokens',
        readonly=True,
        copy=False,
        # compute='_compute_remaining_tokens',
        store=True,
    )
    refill_timestamp = fields.Datetime(string='Next Refill Timestamp', readonly=True, copy=False)

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

    def action_setup_user_token(self):
        self.ensure_one()
        from ..utils.google_utils import setup_user_token
        return setup_user_token(
            self,
            creds_field='google_user_token_json',
            client_config_field='google_client_secrets_json',
            scopes=_DEFAULT_COLAB_SCOPES,
        )

    # OVERRIDE
    # @api.depends('quota_json')
    # def _compute_remaining_tokens(self):
    #     """get remaining tokens"""
    #     for record in self:
    #         if (
    #             record.code == 'colab'
    #             and record.quota_json
    #             and (ccuInfo := record.quota_json.get('freeCcuQuotaInfo'))
    #         ):
    #             record.remaining_tokens = ccuInfo.get('remainingTokens')
    #             if not record.initial_token:
    #                 record.initial_token = record.remaining_tokens
    
    def _check_is_available(self):
        """To be override with other provider"""
        if self.code != 'colab':
            return super()._check_is_available()

        self.ensure_one()

        free_quota = (self.quota_json or {}).get('freeCcuQuotaInfo') or {}

        self.remaining_tokens = free_quota.get('remainingTokens')
        return self.remaining_tokens is not None and self.remaining_tokens > 0

    def get_worker_name(self) -> str:
        if self.code != 'colab':
            return super().get_worker_name()
    
        return f'colab_worker:{self.id}'

    def get_worker(self):
        if self.code != 'colab':
            return super().get_worker()

        try:
            from iantirta.media import ColabWorker
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

        return ColabWorker(access_token=self.google_user_token_json, name=self.get_worker_name())

    def _prepare_folder(self, tmpdir: str, tmp_script_path: Path) -> str:
        if self.code != 'colab':
            return super()._prepare_folder(tmpdir, tmp_script_path)

        return tmp_script_path

    def worker_run(self):
        if self.code != 'colab':
            return super().worker_run()

        env_lines: list[str] = self._prepare_env_params()
        code_lines: list[str] = self.notebook_id.to_source_code()
        source_code = "".join(env_lines + code_lines)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_script_path = Path(tmpdir) / "worker_job.py"

            with open(str(tmp_script_path), "w", encoding="utf-8") as f:
                f.write(source_code)

            self.run_state = 'starting_up'

            dbname = self.env.cr.dbname
            _context = self.env.context
            worker_id = self.id
            try:
                worker = self.get_worker()

                def on_close():
                    remaining = None
                    refill_at = None

                    try:
                        quota = worker.state.client.get_consumption_user_info()
                    except Exception as e:
                        _logger.warning(f"Error while getting consumtion info, Error: {e}")
                        quota = None
                    
                    if quota and quota.freeCcuQuotaInfo:
                        remaining = quota.freeCcuQuotaInfo.remainingTokens
                        refill_at = quota.freeCcuQuotaInfo.nextRefillTimestampSec

                    elif quota:
                        remaining = 0

                    with Registry(dbname).cursor() as new_cr:
                        env = api.Environment(new_cr, SUPERUSER_ID, _context)
                        if record := env['gpu.worker'].browse(worker_id).exists():
                            vals = {'run_state': 'ready'}
                            if remaining is not None:
                                vals['remaining_tokens'] = remaining
                            if refill_at is not None:
                                vals['refill_timestamp'] = refill_at

                            record.write(vals)

                            new_cr.commit()

                            abandoned_tasks = record.karaoke_ids.filtered(
                                lambda k: k.status == 'processing'
                            )
                            if abandoned_tasks:
                                abandoned_tasks.write({
                                    'status': 'waiting',
                                    'worker_id': False
                                })
                            _logger.warning("Closed GPU workers and reset %s abandoned tasks.", len(abandoned_tasks))

                            new_cr.commit()
    
                worker.run(
                    str(tmp_script_path),
                    run_in_background=True,
                    gpu=True,
                    on_close_hook=on_close,
                )

                try:
                    initial_quota = worker.state.client.get_consumption_user_info()
                except Exception as e:
                    _logger.warning(f"Error while getting consumtion info, Error: {e}")
                    initial_quota = None
                
                if initial_quota and initial_quota.freeCcuQuotaInfo:
                    initial_token = initial_quota.freeCcuQuotaInfo.remainingTokens
                    self.write({
                        'initial_token': initial_token,
                        'remaining_tokens': initial_token,
                        'refill_timestamp': initial_quota.freeCcuQuotaInfo.nextRefillTimestampSec,
                    })
            except Exception as e:
                if e.__class__.__name__ == 'ColabRequestError':
                    self.run_state = 'ready'
                    raise
                raise
