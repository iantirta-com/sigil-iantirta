
from sigil import fields, models


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
