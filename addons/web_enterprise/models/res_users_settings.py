from sigil import models, fields, api


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    color_scheme = fields.Selection([
        ('system', 'System'),
        ('light', 'Light'),
        ('dark', 'dark'),],
        required=True,
        store=True,
        default="system",
        string="Color Scheme")

    homemenu_config = fields.Json(
        string="Home Menu Configuration",
        store=True, readonly=True)