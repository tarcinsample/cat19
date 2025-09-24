# -*- coding: utf-8 -*-

from odoo import models, fields

class OpStudent(models.Model):
    _name = 'op.student'
    _description = 'Student'

    name = fields.Char(string='Name', required=True)
