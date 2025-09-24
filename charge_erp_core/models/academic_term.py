# -*- coding: utf-8 -*-

from odoo import fields, models

class OpAcademicTerm(models.Model):
    _name = 'op.academic.term'
    _description = "Academic Term"

    name = fields.Char('Name', required=True)
    term_start_date = fields.Date('Start Date', required=True)
    term_end_date = fields.Date('End Date', required=True)
    academic_year_id = fields.Many2one(
        'op.academic.year', 'Academic Year', required=True)
    parent_term = fields.Many2one('op.academic.term', 'Parent Term')
