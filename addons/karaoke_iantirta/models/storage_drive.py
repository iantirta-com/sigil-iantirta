
import base64

from sigil import api, fields, models


class CloudStorage(models.Model):
    _inherit = 'iantirta.cloud.storage'

    code = fields.Selection(selection_add=[
        ('gdrive', 'Google Drive')
    ], ondelete={'gdrive': 'set default'})

    gdrive_credentials = fields.Binary(
        string="Google Drive Credentials as .json",
        store=False,
        copy=False,
    )
    gdrive_client_config = fields.Char(
        string="Google Drive Client Config",
        compute="_compute_gdrive_client_config",
        readonly=False,
        store=True,
        required_if_provider='gdrive',
        copy=False,
    )
    gdrive_access_token_json = fields.Char(
        copy=False,
    )
    gdrive_root_folder_id = fields.Char(
        'Root Folder ID as where to store in the drive storage.',
        required_if_provider='gdrive',
        copy=False,
    )

    @api.onchange('gdrive_credentials')
    def _compute_gdrive_client_config(self):
        for storage in self:
            if storage.code == 'gdrive':
                creds = storage.with_context(
                    bin_size=False
                ).gdrive_credentials

                storage.gdrive_client_config = (
                    base64.b64decode(creds)
                    if creds else False
                )

    def action_setup_user_token(self):
        self.ensure_one()
        try:
            from iantirta.media import DriveStorage
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

        if (
            not self.gdrive_access_token_json
            or not (creds := DriveStorage.get_credentials(
                self.gdrive_access_token_json
            ))
        ):
            auth_uri, _ = DriveStorage.setup_user_token(
                client_config=self.gdrive_client_config,
                redirect_uri=f"{self.get_base_url().rstrip('/')}/google_drive/callback",
                state=str(self.id),
                key=f'drive_{self.id}'
            )
            return {
                'type': 'ir.actions.act_url',
                'url': auth_uri,
                'target': 'self',
            }
        else:
            self.gdrive_access_token_json = creds.to_json()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Google Drive token refreshed successfully.',
                    'type': 'success',
                    'sticky': False,
                }
            }

    # OVERRIDES
    def action_test_connection(self):
        if self.code != 'gdrive':
            return super().action_test_connection()

        self.ensure_one()
        try:
            from iantirta.media import DriveStorage
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

        api = DriveStorage(
            access_token=self.gdrive_access_token_json,
            root_folder_id=self.gdrive_root_folder_id,
        )
        try:
            api.test_connection()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Google Drive connection success.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            self.state = 'disabled'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Google Drive connection failed: {e}.',
                    'type': 'error',
                    'sticky': False,
                }
            }

    def _prepare_notebook_params(self) -> dict:
        if self.code != 'gdrive':
            return super()._prepare_notebook_params()

        return {
            'provider': self.code,
            'access_token': self.gdrive_access_token_json,
            'root_folder_id': self.gdrive_root_folder_id,
        }
