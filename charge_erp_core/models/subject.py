from odoo import models, fields

class OpSubject(models.Model):
    _name = "op.subject"
    _description = "Subject"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
    subject_type = fields.Selection(
        [('theory', 'Theory'), ('practical', 'Practical'),
         ('other', 'Other')],
        'Subject Type', default="theory", required=True)
    grade_weightage = fields.Float('Grade Weightage', default=1.0)
