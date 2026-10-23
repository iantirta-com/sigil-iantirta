import base64

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
