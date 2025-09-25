# -*- coding: utf-8 -*-

from odoo import models, fields

class OpStudent(models.Model):
    _name = 'op.student'
    _description = 'Student'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete="cascade")

    birth_date = fields.Date(string='Birth Date')
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-')],
        string='Blood Group')
    visa_info = fields.Char(string='Visa Info')
    is_an_alumni = fields.Boolean(string='Is an Alumni?')
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string='Gender', related='partner_id.gender', readonly=False)
    country_id = fields.Many2one(
        'res.country', string='Nationality', related='partner_id.country_id', readonly=False)
    lang = fields.Many2one(
        'res.lang', string='Language', related='partner_id.lang', readonly=False)
