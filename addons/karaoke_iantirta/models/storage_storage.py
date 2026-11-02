# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import logging
from typing import Any

from sigil import fields, models

_logger = logging.getLogger(__name__)


class CloudStorage(models.Model):
    _name = 'iantirta.cloud.storage'
    _description = 'Cloud Storage'

    name = fields.Char(required=True, translate=True)
    code = fields.Selection(
        string="Provider",
        help="The technical code of this storage provider.",
        selection=[],
        required=True,
    )
    access_token = fields.Char(
        copy=False,
    )

    storage_endpoint = fields.Char(compute='_compute_storage_endpoint',)

    # -----------------------
    # Compute method
    # -----------------------

    def _compute_storage_endpoint(self):
        for record in self:
            record.storage_endpoint = record._get_storage_endpoint()
            
    # -----------------------
    # Abstraction method
    # -----------------------
    
    def _get_storage_endpoint(self) -> str:
        """
        Download endpoint for storage endpoint.

        Provider should override this method.

        :return: url string for the base domain download endpoint.
        :rtype: str
        """
        return ''

    # -----------------------
    # Worker run helper and abstraction method
    # -----------------------

    def _prepare_notebook_params(self) -> dict[str, Any]:
        """
        Prepare necessary storage options that will be pass
        along env source code worker run.

        Provider should inherit, add, or override this method

        :return: dictionary data
        :rtype: dict[str, Any]
        """
        return {
            'provider': self.code,
            'access_token': self.access_token,
        }

    # -----------------------
    # Actionable Method
    # -----------------------

    def test_connection(self):
        """
        Actually test connection to the storage api.

        Provider should override this method.
        """
        raise NotImplementedError()

    # -----------------------
    # User Action
    # -----------------------
    
    def action_test_connection(self):
        """
        Action method to test connection to the storage api.
        """
        self.ensure_one()

        params = {
            'message': 'Connection success.',
            'type': 'success',
            'sticky': False,
        }
        try:
            self.test_connection()
        except Exception as e:
            _logger.exception(f"Exception during test connection: Error: {e}")
            params.update({
                'message': 'Connection failed',
                'type': 'danger'
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': params,
        }
