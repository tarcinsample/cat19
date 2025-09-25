from odoo import models, fields

class OpProgram(models.Model):
    _name = "op.program"
    _description = "Program"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
    level_id = fields.Many2one('op.program.level', 'Program Level')
    department_id = fields.Many2one('op.department', 'Department')
