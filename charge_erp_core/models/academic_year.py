from odoo import models, fields

class OpAcademicYear(models.Model):
    _name = "op.academic.year"
    _description = "Academic Year"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    term_ids = fields.One2many(
        'op.academic.term', 'academic_year_id', 'Terms')
