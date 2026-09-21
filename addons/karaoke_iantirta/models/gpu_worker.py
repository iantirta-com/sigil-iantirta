import logging

from sigil import _, api, fields, models
from sigil.exceptions import UserError

_logger = logging.getLogger(__name__)


class GpuWorker(models.Model):
    _name = 'gpu.worker'
    _description = 'GPU Worker'

    name = fields.Char(required=True)

    provider = fields.Selection([
        ("kaggle", "Kaggle")
    ], required=True)

    access_token = fields.Char(
        string="Kaggle API Token", required=True,
        help='https://www.kaggle.com/settings/api (click "Generate New Token" under "API")'
    )

    quota_json = fields.Json(compute="_compute_quotas", store=True)

    # Helper
    _worker = None

    def _get_worker_class(self):
        from .kplus_tools import KaggleWorker
        provider_map = {
            "kaggle": KaggleWorker
        }
        return provider_map.get(self.provider, None)

    def _get_worker_instance(self):
        self.ensure_one()
        if instance := self._get_worker_class():
            return instance(self.access_token)
        raise UserError(_("Unsupported provider configuration."))

    def get_quotas(self) -> dict:
        quotas = self._get_worker_instance().get_quota()
        self.quota_json = quotas
        return quotas

    @api.depends("access_token", 'name', "provider")
    def _compute_quotas(self):
        for record in self:
            if record.access_token:
                try:
                    record.get_quotas()
                except Exception as e:
                    _logger.error("Failed to fetch quotas for %s: %s", record.name, e)
                    record.quota_json = {
                        "error": "Failed to fetch quotas",
                        "error_str": str(e),
                    }
            else:
                record.quota_json = {}

    def action_get_quotas(self):
        return self.get_quotas()

    def action_run(self):
        worker = self._get_worker_instance()
        worker.run()