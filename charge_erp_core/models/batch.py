from odoo import models, fields

class OpBatch(models.Model):
    _name = "op.batch"
    _description = "Batch"

    name = fields.Char('Name', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    course_id = fields.Many2one('op.course', 'Course', required=True)
