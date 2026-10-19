
import base64

from sigil import fields, models, api, _
from sigil.exceptions import UserError, ValidationError


class CloudStorage(models.Model):
    _name = 'iantirta.cloud.storage'
    _description = 'Cloud Storage'

    def _valid_field_parameter(self, field, name):
        return name == 'required_if_provider' or super()._valid_field_parameter(field, name)

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Selection(
        string="Provider",
        help="The technical code of this storage provider.",
        selection=[('none', "No Provider Set")],
        default='none',
        required=True,
    )

    state = fields.Selection(
        string="State",
        help="In test mode, a fake storage is processed through a test storage interface.\n"
             "This mode is advised when setting up the provider.",
        selection=[('disabled', "Disabled"), ('enabled', "Enabled"), ('test', "Test Mode")],
        default='disabled', required=True, copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        storages = super().create(vals_list)
        storages._check_required_if_provider()

        return storages

    def write(self, vals):
        result = super().write(vals)
        self._check_required_if_provider()

        return result

    def _check_required_if_provider(self):
        """ Check that provider-specific required fields have been filled.

        The fields that have the `required_if_provider='<provider_code>'` attribute are made
        required for all `iantirta.cloud.storage` records with the `code` field equal to `<provider_code>`
        and with the `state` field equal to `'enabled'` or `'test'`.

        Provider-specific views should make the form fields required under the same conditions.

        :return: None
        :raise ValidationError: If a provider-specific required field is empty.
        """
        field_names = []
        enabled_storages = self.filtered(
            lambda p: p.state in ['enabled', 'test']
        )
        for field_name, field in self._fields.items():
            required_for_provider_code = getattr(field, 'required_if_provider', None)
            if required_for_provider_code and any(
                required_for_provider_code == storage._get_code() and not storage[field_name]
                for storage in enabled_storages
            ):
                ir_field = self.env['ir.model.fields']._get(self._name, field_name)
                field_names.append(ir_field.field_description)
        if field_names:
            raise ValidationError(
                _("The following fields must be filled: %s", ", ".join(field_names))
            )

    def _get_code(self):
        """ Return the code of the provider.

        Note: `self.ensure_one()`

        :return: The code of the provider.
        :rtype: str
        """
        self.ensure_one()
        return self.code

    def action_test_connection(self):
        raise NotImplementedError()

# 
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
            or not (creds := DriveStorage.get_gdrive_credentials(
                    self.gdrive_access_token_json
            ))
        ):
            auth_uri, _ = DriveStorage.request_gdrive_user_token_auth_url(
                self.gdrive_client_config,
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
            user_token=self.gdrive_access_token_json,
            root_folder_id=self.gdrive_root_folder_id,
        )
        if api.test_connection():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Google Drive connection success.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Google Drive connection failed.',
                    'type': 'error',
                    'sticky': False,
                }
            }
        

class CloudStorage(models.Model):
    _inherit = 'iantirta.cloud.storage'

    code = fields.Selection(selection_add=[
        ('hf_dataset', 'Huggingface Dataset')
    ], ondelete={'hf_dataset': 'set default'})

    hf_repo_id = fields.Char(
        required_if_provider='hf_dataset',
        copy=False,
    )
    hf_access_token = fields.Char(
        required_if_provider='hf_dataset',
        copy=False,
    )
