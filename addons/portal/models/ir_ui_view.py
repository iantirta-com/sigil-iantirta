# -*- coding: utf-8 -*-

from sigil import models, fields


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    customize_show = fields.Boolean("Show As Optional Inherit", default=False)
