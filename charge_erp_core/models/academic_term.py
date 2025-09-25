from odoo import models, fields

class OpAcademicTerm(models.Model):
    _name = "op.academic.term"
    _description = "Academic Term"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
    academic_year_id = fields.Many2one(
        'op.academic.year', 'Academic Year', required=True)
