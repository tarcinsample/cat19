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
    """Faculty model for OpenEduCat.

    This model manages faculty members within the institution,
    including their personal information, department assignments,
    and subject associations.

    Attributes:
        partner_id (int): Reference to the associated partner record
        first_name (str): Faculty member's first name
        middle_name (str): Faculty member's middle name
        last_name (str): Faculty member's last name
        birth_date (date): Date of birth
        blood_group (str): Blood group type
        gender (str): Gender of the faculty member
        nationality (int): Reference to country of nationality
        emergency_contact (int): Reference to emergency contact partner
        visa_info (str): Visa information
        id_number (str): ID card number
        faculty_subject_ids (list): List of subjects taught by the faculty
        emp_id (int): Reference to HR employee record
        main_department_id (int): Primary department assignment
        allowed_department_ids (list): List of departments faculty can access
    """

    _name = "op.faculty"
    _description = "OpenEduCat Faculty"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}
    _parent_name = False
    _order = "name"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete="cascade",
        tracking=True
    )
    
    first_name = fields.Char(
        string='First Name',
        required=True,
        translate=True,
        tracking=True
    )
    
    middle_name = fields.Char(
        string='Middle Name',
        size=128,
        tracking=True
    )
    
    last_name = fields.Char(
        string='Last Name',
        size=128,
        required=True,
        tracking=True
    )
    
    birth_date = fields.Date(
        string='Birth Date',
        required=True,
        tracking=True
    )
    
    blood_group = fields.Selection([
        ('A+', 'A+ve'),
        ('B+', 'B+ve'),
        ('O+', 'O+ve'),
        ('AB+', 'AB+ve'),
        ('A-', 'A-ve'),
        ('B-', 'B-ve'),
        ('O-', 'O-ve'),
        ('AB-', 'AB-ve')
    ], string='Blood Group', tracking=True)
    
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Gender', required=True, tracking=True)
    
    nationality = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        tracking=True
    )
    
    emergency_contact = fields.Many2one(
        comodel_name='res.partner',
        string='Emergency Contact',
        tracking=True
    )
    
    visa_info = fields.Char(
        string='Visa Info',
        size=64,
        tracking=True
    )
    
    id_number = fields.Char(
        string='ID Card Number',
        size=64,
        tracking=True
    )
    
    login = fields.Char(
        string='Login',
        related='partner_id.user_id.login',
        readonly=True
    )
    
    last_login = fields.Datetime(
        string='Latest Connection',
        readonly=True,
        related='partner_id.user_id.login_date'
    )
    
    faculty_subject_ids = fields.Many2many(
        comodel_name='op.subject',
        string='Subject(s)',
        tracking=True
    )
    
    emp_id = fields.Many2one(
        comodel_name='hr.employee',
        string='HR Employee',
        tracking=True
    )
    
    main_department_id = fields.Many2one(
        comodel_name='op.department',
        string='Main Department',
        default=lambda self: self.env.user.dept_id.id or False,
        tracking=True
    )
    
    allowed_department_ids = fields.Many2many(
        comodel_name='op.department',
        string='Allowed Department',
        default=lambda self: self.env.user.department_ids.ids or False,
        tracking=True
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True
    )

    _sql_constraints = [
        ('unique_id_number',
         'unique(id_number)',
         'ID Card Number must be unique!')
    ]

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """Validate that birth date is not in the future.

        Raises:
            ValidationError: If birth date is greater than current date.
        """
        for record in self:
            if record.birth_date > fields.Date.today():
                raise ValidationError(_(
                    "Birth Date can't be greater than current date!"))

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_name(self):
        """Update the name field based on first, middle, and last names."""
        if not self.middle_name:
            self.name = f"{self.first_name} {self.last_name}"
        else:
            self.name = f"{self.first_name} {self.middle_name} {self.last_name}"

    def create_employee(self):
        """Create an HR employee record for the faculty member.

        Creates a new employee record and updates the faculty record
        with the employee reference.
        """
        for record in self:
            vals = {
                'name': record.name,
                'country_id': record.nationality.id,
                'gender': record.gender,
            }
            emp_id = self.env['hr.employee'].create(vals)
            record.write({'emp_id': emp_id.id})
            record.partner_id.write({
                'partner_share': True,
                'employee': True
            })

    @api.model
    def get_import_templates(self):
        """Get the import template for faculty data.

        Returns:
            list: List containing template information
        """
        return [{
            'label': _('Import Template for Faculties'),
            'template': '/openeducat_core/static/xls/op_faculty.xls'
        }]


class PartnerTitle(models.Model):
    """Extension of res.partner.title model.

    This model extends the partner title model to customize
    the display name format.
    """

    _inherit = 'res.partner.title'

    @api.depends('shortcut')
    def _compute_display_name(self):
        """Compute the display name based on the shortcut.

        Sets the display name to be the same as the shortcut.
        """
        for record in self:
            record.display_name = record.shortcut
