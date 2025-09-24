# -*- coding: utf-8 -*-

from odoo import fields, models

class OpAcademicYear(models.Model):
    _name = 'op.academic.year'
    _description = "Academic Year"

    name = fields.Char('Name', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    term_structure = fields.Selection([('two_sem', 'Two Semesters'),
                                       ('two_sem_qua', 'Two Semesters subdivided by Quarters'),
                                       ('two_sem_final', 'Two Semesters subdivided by Quarters and Final Exams'),
                                       ('three_sem', 'Three Trimesters'),
                                       ('four_Quarter', 'Four Quarters'),
                                       ('final_year', 'Final Year Grades subdivided by Quarters'),
                                       ('others', 'Other(overlapping terms, custom schedules)')],
                                      string='Term Structure', default='two_sem', required=True)
    academic_term_ids = fields.One2many('op.academic.term', 'academic_year_id', string='Academic Terms')
    active = fields.Boolean(default=True)
