# -*- coding: utf-8 -*-

from sigil import fields, models


class FleetVehicleTag(models.Model):
    _name = 'fleet.vehicle.tag'
    _description = 'Vehicle Tag'

    name = fields.Char('Tag Name', required=True, translate=True)
    color = fields.Integer('Color')

    _name_uniq = models.Constraint(
        'unique (name)',
        'Tag name already exists!',
    )
