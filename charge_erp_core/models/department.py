# -*- coding: utf-8 -*-

from odoo import fields, models

class OpDepartment(models.Model):
    _name = "op.department"
    _description = "Department"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    parent_id = fields.Many2one('op.department', 'Parent Department')
