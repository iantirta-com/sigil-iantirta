# from sigil import models, fields, api


# class web_enterprise_iantirta(models.Model):
#     _name = 'web_enterprise_iantirta.web_enterprise_iantirta'
#     _description = 'web_enterprise_iantirta.web_enterprise_iantirta'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

