# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import base64

from sigil import _, api, fields, models
from sigil.exceptions import UserError

_DEFAULT_DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']


class CloudStorage(models.Model):
    _inherit = 'iantirta.cloud.storage'

    code = fields.Selection(selection_add=[
        ('gdrive', 'Google Drive')
    ], ondelete={'gdrive': 'cascade'})

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

    gdrive_root_folder_id = fields.Char(
        help='Root Folder ID as where to store in the drive storage.',
        copy=False,
    )

    # -----------------------
    # Compute method
    # -----------------------

    @api.onchange('google_client_secrets')
    def _compute_google_client_secrets_json(self):
        for record in self:
            if record.code == 'gdrive':
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
            scopes=_DEFAULT_DRIVE_SCOPES,
        )

    # Override

    # -----------------------
    # Abstraction method
    # -----------------------

    # -----------------------
    # Worker run helper and abstraction method
    # -----------------------
    
    def _prepare_notebook_params(self) -> dict:
        """
        Prepare necessary storage options that will be pass
        along env source code worker run.

        In gdrive, we needed root_folder_id to act as a root storage

        :return: dictionary data
        :rtype: dict[str, Any]
        """
        params = super()._prepare_notebook_params()

        if self.code != 'gdrive':
            return params

        if not self.gdrive_root_folder_id:
            raise UserError(_("root folder id is required."))

        return {
            **params,
            'root_folder_id': self.gdrive_root_folder_id,
        }

    # -----------------------
    # Actionable Method
    # -----------------------

    def test_connection(self):
        """
        Actually test connection to the storage api.

        Provider should override this method.
        """
        if self.code != 'gdrive':
            return super().test_connection()

        if not self.gdrive_root_folder_id:
            raise UserError(_("root folder id is required."))

        self.ensure_one()

        try:
            from iantirta.media import DriveStorage
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Cannot Continue as iantirta-media is not installed"
            )

        return DriveStorage(
            access_token=self.access_token,
            root_folder_id=self.gdrive_root_folder_id,
        ).test_connection()
