from sigil import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    color_scheme = fields.Selection(related="res_users_settings_id.color_scheme")
    