# -*- coding: utf-8 -*-

from odoo import models, fields

class OpProgramLevel(models.Model):
    _name = "op.program.level"
    _description = "Program Level"

    name = fields.Char('Name', required=True, translate=True)

    _sql_constraints = [
        ('unique_level_name', 'unique(name)', 'Name should be unique per Program level!')
    ]
