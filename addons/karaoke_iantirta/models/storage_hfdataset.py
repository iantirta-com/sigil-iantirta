# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

from sigil import _, api, fields, models
from sigil.exceptions import UserError


class CloudStorage(models.Model):
    _inherit = 'iantirta.cloud.storage'

    code = fields.Selection(selection_add=[
        ('hf_dataset', 'Huggingface Dataset')
    ], ondelete={'hf_dataset': 'cascade'})

    hf_repo_id = fields.Char(
        copy=False,
    )

    # -----------------------
    # Compute method
    # -----------------------

    @api.depends('hf_repo_id')
    def _compute_storage_endpoint(self):
        super()._compute_storage_endpoint()

    # Override

    # -----------------------
    # Abstraction method
    # -----------------------

    def _get_storage_endpoint(self) -> str:
        """
        Download endpoint for storage endpoint.

        :return: url string for the base domain download endpoint.
        :rtype: str
        """
        if self.code != 'hf_dataset':
            return super()._get_storage_endpoint()

        return (
            'https://huggingface.co/'
            'datasets/'
            + self.hf_repo_id.strip('/') +
            '/resolve/main/'
        )

    # -----------------------
    # Worker run helper and abstraction method
    # -----------------------

    def _prepare_notebook_params(self) -> dict:
        """
        Prepare necessary storage options that will be pass
        along env source code worker run.

        In hf dataset, we need repo_id.

        :return: dictionary data
        :rtype: dict[str, Any]
        """
        params = super()._prepare_notebook_params()

        if self.code != 'hf_dataset':
            return params

        if not self.hf_repo_id:
            raise UserError(_("hf repo id is required."))

        return {
            **params,
            'repo_id': self.hf_repo_id,
        }

    # -----------------------
    # Actionable Method
    # -----------------------

    def test_connection(self):
        """
        Actually test connection to the storage api.

        Provider should override this method.
        """
        if self.code != 'hf_dataset':
            return super().test_connection()

        if not self.hf_repo_id:
            raise UserError(_("hf repo id is required."))

        self.ensure_one()

        try:
            from iantirta.media import HFDatasetStorage
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Cannot Continue as iantirta-media is not installed"
            )

        return HFDatasetStorage(
            access_token=self.access_token,
            repo_id=self.hf_repo_id,
        ).test_connection()
