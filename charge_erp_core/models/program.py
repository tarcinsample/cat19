# -*- coding: utf-8 -*-

from odoo import models, fields

class OpProgram(models.Model):
    _name = "op.program"
    _description = "Program"

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', size=16, required=True, translate=True)
    max_unit_load = fields.Float("Maximum Unit Load")
    min_unit_load = fields.Float("Minimum Unit Load")
    active = fields.Boolean(default=True)
    image_1920 = fields.Image('Image', attachment=True)
    program_level_id = fields.Many2one(
        'op.program.level', 'Program Level', required=True)

    _sql_constraints = [
        ('unique_program_code', 'unique(code)', 'Code should be unique per program!')
    ]
