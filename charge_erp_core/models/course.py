from odoo import models, fields

class OpCourse(models.Model):
    _name = "op.course"
    _description = "Course"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', size=16, required=True)
    parent_id = fields.Many2one('op.course', 'Parent Course')
    evaluation_type = fields.Selection(
        [('normal', 'Normal'), ('gpa', 'GPA')],
        'Evaluation Type', default="normal", required=True)
