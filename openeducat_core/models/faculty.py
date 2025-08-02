###############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<https://www.openeducat.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpFaculty(models.Model):
    _name = "op.faculty"
    _description = "OpenEduCat Faculty"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}
    _parent_name = False

    partner_id = fields.Many2one('res.partner', 'Partner',
                                 required=True, ondelete="cascade")
    first_name = fields.Char('First Name', translate=True, required=True)
    middle_name = fields.Char('Middle Name', size=128)
    last_name = fields.Char('Last Name', size=128, required=True)
    birth_date = fields.Date('Birth Date', required=True)
    blood_group = fields.Selection([
        ('A+', 'A+ve'),
        ('B+', 'B+ve'),
        ('O+', 'O+ve'),
        ('AB+', 'AB+ve'),
        ('A-', 'A-ve'),
        ('B-', 'B-ve'),
        ('O-', 'O-ve'),
        ('AB-', 'AB-ve')
    ], string='Blood Group')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], 'Gender', required=True)
    nationality = fields.Many2one('res.country', 'Nationality')
    emergency_contact = fields.Many2one(
        'res.partner', 'Emergency Contact')
    visa_info = fields.Char('Visa Info', size=64)
    id_number = fields.Char('ID Card Number', size=64)
    login = fields.Char(
        'Login', related='partner_id.user_id.login', readonly=True)
    last_login = fields.Datetime('Latest Connection', readonly=True,
                                 related='partner_id.user_id.login_date')
    faculty_subject_ids = fields.Many2many('op.subject', string='Subject(s)',
                                           tracking=True,
                                           help="Subjects that this faculty member can teach")
    emp_id = fields.Many2one('hr.employee', 'HR Employee')
    main_department_id = fields.Many2one(
        'op.department', 'Main Department',
        default=lambda self:
        self.env.user.dept_id and self.env.user.dept_id.id or False)
    allowed_department_ids = fields.Many2many(
        'op.department', string='Allowed Department',
        default=lambda self:
        self.env.user.department_ids and self.env.user.department_ids.ids or False)
    active = fields.Boolean(default=True)

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """Validate faculty birth date is not in the future.
        
        Raises:
            ValidationError: If birth date is greater than current date
        """
        for record in self:
            if record.birth_date and record.birth_date > fields.Date.today():
                raise ValidationError(_(
                    "Birth Date can't be greater than current date!"))

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_name(self):
        """Compute full name from first, middle, and last names."""
        if self.first_name and self.last_name:
            if self.middle_name:
                self.name = f"{self.first_name} {self.middle_name} {self.last_name}"
            else:
                self.name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.name = self.first_name
        elif self.last_name:
            self.name = self.last_name
        else:
            self.name = False

    def create_employee(self):
        """Create HR employee record for faculty members.
        
        Creates a linked hr.employee record with basic information from faculty.
        Updates the partner record to mark as employee.
        """
        for record in self:
            vals = {
                'name': record.name,
                'country_id': record.nationality.id,
                'gender': record.gender,
            }
            emp_id = self.env['hr.employee'].create(vals)
            record.write({'emp_id': emp_id.id})
            record.partner_id.write({'partner_share': True, 'employee': True})

    @api.model
    def get_import_templates(self):
        """Get import template for bulk faculty data import.
        
        Returns:
            list: Dictionary containing template label and file path
        """
        return [{
            'label': _('Import Template for Faculties'),
            'template': '/openeducat_core/static/xls/op_faculty.xls'
        }]

    class PartnerTitle(models.Model):
        _inherit = 'res.partner.title'

        @api.depends('shortcut')
        def _compute_display_name(self):
            for record in self:
                record.display_name = f"{record.shortcut}"
