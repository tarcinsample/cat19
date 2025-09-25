from odoo import models, fields

class OpFaculty(models.Model):
    _name = "op.faculty"
    _description = "Faculty"
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete='cascade')

    faculty_id = fields.Char('Faculty ID', size=16, required=True)
