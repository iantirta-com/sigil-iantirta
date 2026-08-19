# from sigil import models, fields, api


# class web_iantirta(models.Model):
#     _name = 'web_iantirta.web_iantirta'
#     _description = 'web_iantirta.web_iantirta'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

