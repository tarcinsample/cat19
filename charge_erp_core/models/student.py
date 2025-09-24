# -*- coding: utf-8 -*-

from odoo import models, fields

class OpStudent(models.Model):
    _name = 'op.student'
    _description = 'Student'

    name = fields.Char(string='Name', required=True)
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string='Gender')
    birth_date = fields.Date(string='Birth Date')
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-')],
        string='Blood Group')
    visa_info = fields.Char(string='Visa Info')
    is_an_alumni = fields.Boolean(string='Is an Alumni?')
    nationality = fields.Many2one('res.country', string='Nationality')
    lang = fields.Many2one('res.lang', string='Language')
