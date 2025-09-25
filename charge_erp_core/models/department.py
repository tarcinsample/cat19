from odoo import models, fields

class OpDepartment(models.Model):
    _name = "op.department"
    _description = "Department"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
