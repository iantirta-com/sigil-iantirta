from sigil import api, fields, models


class GpuWorkerLog(models.Model):
    _name = 'gpu.worker.log'
    _description = 'GPU Worker Log'
    _order = 'id DESC'
    _allow_sudo_commands = False

    name = fields.Char(required=True)
    type = fields.Selection([('client', 'Client'), ('server', 'Server')], required=True, index=True)
    dbname = fields.Char(string='Database Name', index=True)
    level = fields.Char(index=True)
    message = fields.Text(required=True)
    path = fields.Char(required=True)
    func = fields.Char(string='Function', required=True)
    line = fields.Char(required=True)

    worker_id = fields.Many2one('gpu.worker', string='Worker', required=True, ondelete='cascade')
    