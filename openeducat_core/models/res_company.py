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

from odoo import fields, models


class ResCompany(models.Model):
    """Extension of the Company model.

    This model extends the standard company model to add
    educational institution specific fields.

    Attributes:
        signature (binary): Company signature image
        accreditation (str): Accreditation information
        approval_authority (str): Approval authority details
    """

    _inherit = "res.company"

    signature = fields.Binary(
        string='Signature',
        help="Company signature image"
    )
    
    accreditation = fields.Text(
        string='Accreditation',
        help="Accreditation information for the institution"
    )
    
    approval_authority = fields.Text(
        string='Approval Authority',
        help="Details of the approval authority"
    )


class ResUsers(models.Model):
    """Extension of the Users model.

    This model extends the standard users model to add
    educational institution specific functionality and fields.

    Attributes:
        student_line (int): Reference to associated student record
        user_line (list): List of associated student records
        child_ids (list): List of child user records
        dept_id (int): Reference to primary department
        department_ids (list): List of allowed departments
        department_count (int): Number of departments
    """

    _inherit = "res.users"
    _parent_name = False

    student_line = fields.Many2one(
        comodel_name='op.student',
        string='Line',
        help="Associated student record"
    )
    
    user_line = fields.One2many(
        comodel_name='op.student',
        inverse_name='user_id',
        string='User Line',
        help="Associated student records"
    )
    
    child_ids = fields.Many2many(
        comodel_name='res.users',
        relation='res_user_first_rel1',
        column1='user_id',
        column2='res_user_second_rel1',
        string='Childs',
        help="Child user records"
    )
    
    dept_id = fields.Many2one(
        comodel_name='op.department',
        string='Department Name',
        help="Primary department assignment"
    )
    
    department_ids = fields.Many2many(
        comodel_name='op.department',
        string='Allowed Department',
        help="List of departments the user can access"
    )
    
    department_count = fields.Integer(
        compute='_compute_department_count',
        string="Number of Departments",
        default=lambda self: self._department_count(),
        help="Total number of departments"
    )

    def _department_count(self):
        """Get the total number of departments.

        Returns:
            int: Total number of departments
        """
        return self.env['op.department'].sudo().search_count([])

    def create_user(self, records, user_group=None):
        """Create user records for given records.

        Creates user records for the given records and optionally
        adds them to a user group.

        Args:
            records (list): List of records to create users for
            user_group (res.groups): Optional user group to add users to
        """
        for rec in records:
            if not rec.user_id:
                user_vals = {
                    'name': rec.name,
                    'login': rec.email or (rec.name + rec.last_name),
                    'partner_id': rec.partner_id.id,
                    'dept_id': rec.main_department_id.id,
                    'department_ids': rec.allowed_department_ids.ids
                }
                user_id = self.create(user_vals)
                rec.user_id = user_id
                if user_group:
                    user_group.users = user_group.users + user_id

    def _compute_department_count(self):
        """Compute the total number of departments.

        Updates the department_count field for all users.
        """
        department_count = self._department_count()
        for user in self:
            user.department_count = department_count
