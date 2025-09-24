# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class OpFaculty(models.Model):
    _name = "op.faculty"
    _description = "Faculty"

    first_name = fields.Char('First Name', translate=True, required=True)
    middle_name = fields.Char('Middle Name', size=128)
    last_name = fields.Char('Last Name', size=128, required=True)
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    birth_date = fields.Date('Birth Date', required=True)
    blood_group = fields.Selection([
        ('A+', 'A+ve'), ('B+', 'B+ve'), ('O+', 'O+ve'), ('AB+', 'AB+ve'),
        ('A-', 'A-ve'), ('B-', 'B-ve'), ('O-', 'O-ve'), ('AB-', 'AB-ve')
    ], string='Blood Group')
    gender = fields.Selection([
        ('male', 'Male'), ('female', 'Female')
    ], 'Gender', required=True)
    nationality = fields.Many2one('res.country', 'Nationality')
    active = fields.Boolean(default=True)

    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_name(self):
        for record in self:
            fname = record.first_name or ""
            mname = record.middle_name or ""
            lname = record.last_name or ""
            record.name = " ".join(filter(None, [fname, mname, lname]))

    @api.constrains('birth_date')
    def _check_birthdate(self):
        for record in self:
            if record.birth_date and record.birth_date > fields.Date.today():
                raise ValidationError(_("Birth Date can't be greater than current date!"))
