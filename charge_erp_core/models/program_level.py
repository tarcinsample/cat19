from odoo import models, fields

class OpProgramLevel(models.Model):
    _name = "op.program.level"
    _description = "Program Level"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
