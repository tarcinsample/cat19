# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class OpBatch(models.Model):
    _name = "op.batch"
    _description = "Batch"

    name = fields.Char('Name', size=32, required=True)
    code = fields.Char('Code', size=16, required=True)
    start_date = fields.Date(
        'Start Date', required=True, default=fields.Date.today())
    end_date = fields.Date('End Date', required=True)
    course_id = fields.Many2one('op.course', 'Course', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_batch_code', 'unique(code)', 'Code should be unique per batch!')
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(
                    _("End Date cannot be set before Start Date."))
