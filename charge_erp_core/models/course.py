# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class OpCourse(models.Model):
    _name = "op.course"
    _description = "Course"

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', size=16, required=True)
    parent_id = fields.Many2one('op.course', 'Parent Course', index=True, ondelete='cascade')
    evaluation_type = fields.Selection(
        [('normal', 'Normal'), ('GPA', 'GPA'),
         ('CWA', 'CWA'), ('CCE', 'CCE')],
        'Evaluation Type', default="normal", required=True)
    active = fields.Boolean(default=True)

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive courses.'))
