import base64
import json
from pathlib import Path
import tempfile

from sigil import api, fields, models

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

    @api.onchange('google_client_secrets')
    def _compute_google_client_secrets_json(self):
        for provider in self:
            if provider.code == 'colab':
                creds = provider.with_context(
                    bin_size=False
                ).google_client_secrets

                provider.google_client_secrets_json = (
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
    def post_vacuum(self):
        for worker in self:
            worker.get_worker().close()

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

    def action_run(self):
        if self.code != 'colab':
            return super().action_run()

        env_lines: list[str] = self._prepare_env_params()
        code_lines: list[str] = self.notebook_id.to_source_code()
        source_code = "".join(env_lines + code_lines)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_script_path = Path(tmpdir) / "worker_job.py"

            with open(str(tmp_script_path), "w", encoding="utf-8") as f:
                f.write(source_code)

            self.run_state = 'starting_up'
            self.get_worker().run(str(tmp_script_path))
