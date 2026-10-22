
from sigil import _, api, fields, models
from sigil.exceptions import ValidationError


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
        selection=[('disabled', "Disabled"), ('enabled', "Enabled")],
        default='disabled', required=True, copy=False
    )

    storage_endpoint = fields.Char(compute='_compute_storage_endpoint',)

    def _compute_storage_endpoint(self):
        for record in self:
            record.storage_endpoint = record._get_storage_endpoint()
            
    def _get_storage_endpoint(self):
        return ''

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
            lambda p: p.state in ['enabled',]
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

    def _prepare_notebook_params(self) -> dict:
        raise NotImplementedError()
