# -*- coding: utf-8 -*-

from sigil import api, fields, models


class ResUsersLog(models.Model):
    _inherit = 'res.users.log'

    ip = fields.Char(string="IP Address")
