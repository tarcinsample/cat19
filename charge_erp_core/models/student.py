from odoo import models, fields

class OpStudent(models.Model):
    _name = "op.student"
    _description = "Student"
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete='cascade')

    student_id = fields.Char('Student ID', size=16, required=True)
