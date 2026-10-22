
from sigil import fields, models, api


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

    @api.depends('hf_repo_id')
    def _compute_storage_endpoint(self):
        super()._compute_storage_endpoint()

    def _get_storage_endpoint(self):
        if self.code != 'hf_dataset':
            return super()._get_storage_endpoint()

        self.storage_endpoint = (
            'https://huggingface.co/'
            'datasets/'
            + self.hf_repo_id.strip('/') +
            '/resolve/main/'
        )

    def action_test_connection(self):
        if self.code != 'hf_dataset':
            return super().action_test_connection()

        self.ensure_one()
        try:
            from iantirta.media import HFDatasetStorage
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

        api = HFDatasetStorage(
            access_token=self.hf_access_token,
            repo_id=self.hf_repo_id,
        )
        try:
            api.test_connection()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Huggingface connection success.',
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
                    'message': f'Huggingface connection failed: {e}.',
                    'type': 'error',
                    'sticky': False,
                }
            }

    def _prepare_notebook_params(self) -> dict:
        if self.code != 'hf_dataset':
            return super()._prepare_notebook_params()

        return {
            'provider': self.code,
            'access_token': self.hf_access_token,
            'repo_id': self.hf_repo_id,
        }
