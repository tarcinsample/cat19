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

from typing import List, Dict, Any
from odoo import _, api, fields, models


class OpSubject(models.Model):
    """Subject model for managing educational subjects.

    This model represents subjects that can be taught in educational institutions.
    It includes information about subject name, code, type, and department association.

    Attributes:
        name (str): Name of the subject
        code (str): Unique code identifier for the subject
        grade_weightage (float): Weightage of the subject in grade calculation
        type (str): Type of subject (theory/practical/both/other)
        subject_type (str): Whether subject is compulsory or elective
        department_id (int): Reference to the department offering the subject
        active (bool): Whether the subject is active
    """

    _name = "op.subject"
    _inherit = "mail.thread"
    _description = "Subject"
    _order = "name"

    name = fields.Char(
        string='Name',
        required=True,
        size=128,
        tracking=True,
        help="Name of the subject"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=256,
        tracking=True,
        help="Unique code identifier for the subject"
    )
    
    grade_weightage = fields.Float(
        string='Grade Weightage',
        tracking=True,
        help="Weightage of the subject in grade calculation"
    )
    
    type = fields.Selection(
        selection=[
            ('theory', 'Theory'),
            ('practical', 'Practical'),
            ('both', 'Both'),
            ('other', 'Other')
        ],
        string='Type',
        required=True,
        default="theory",
        tracking=True,
        help="Type of subject delivery"
    )
    
    subject_type = fields.Selection(
        selection=[
            ('compulsory', 'Compulsory'),
            ('elective', 'Elective')
        ],
        string='Subject Type',
        required=True,
        default="compulsory",
        tracking=True,
        help="Whether the subject is compulsory or elective"
    )
    
    department_id = fields.Many2one(
        comodel_name='op.department',
        string='Department',
        tracking=True,
        default=lambda self: self.env.user.dept_id.id if self.env.user.dept_id else False,
        help="Department offering the subject"
    )
    
    active = fields.Boolean(
        default=True,
        help="If unchecked, the subject will be hidden from the system"
    )

    _sql_constraints = [
        ('unique_subject_code',
         'unique(code)',
         'Subject code must be unique!')
    ]

    @api.model
    def get_import_templates(self) -> List[Dict[str, Any]]:
        """Get the import template for subjects.

        Returns:
            List[Dict[str, Any]]: List containing template information
        """
        return [{
            'label': _('Import Template for Subjects'),
            'template': '/openeducat_core/static/xls/op_subject.xls'
        }]

    @api.constrains('grade_weightage')
    def _check_grade_weightage(self):
        """Validate that grade weightage is not negative."""
        for record in self:
            if record.grade_weightage < 0:
                raise models.ValidationError(_("Grade weightage cannot be negative."))
