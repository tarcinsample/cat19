# -*- coding: utf-8 -*-

from odoo import models, fields

class OpSubject(models.Model):
    _name = "op.subject"
    _description = "Subject"

    name = fields.Char('Name', size=128, required=True)
    code = fields.Char('Code', size=256, required=True)
    grade_weightage = fields.Float('Grade Weightage')
    type = fields.Selection(
        [('theory', 'Theory'), ('practical', 'Practical'),
         ('both', 'Both'), ('other', 'Other')],
        'Type', default="theory", required=True)
    subject_type = fields.Selection(
        [('compulsory', 'Compulsory'), ('elective', 'Elective')],
        'Subject Type', default="compulsory", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_subject_code', 'unique(code)', 'Code should be unique per subject!')
    ]
