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

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OpDepartment(models.Model):
    """Department model for OpenEduCat.

    This model manages academic departments within the institution,
    including their hierarchical structure and relationships.

    Attributes:
        name (str): Name of the department
        code (str): Unique code identifier for the department
        parent_id (int): Reference to parent department for hierarchical structure
    """

    _name = "op.department"
    _description = "OpenEduCat Department"
    _inherit = "mail.thread"
    _order = "name"

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Name of the department"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help="Unique code identifier for the department"
    )
    
    parent_id = fields.Many2one(
        comodel_name='op.department',
        string='Parent Department',
        tracking=True,
        help="Parent department in the hierarchical structure"
    )

    _sql_constraints = [
        ('unique_code',
         'unique(code)',
         'Department code must be unique!')
    ]

    @api.constrains('parent_id')
    def _check_parent_id(self):
        """Validate that a department cannot be its own parent.

        Raises:
            ValidationError: If a department is set as its own parent.
        """
        for record in self:
            if record.parent_id and record.parent_id.id == record.id:
                raise ValidationError(_("A department cannot be its own parent!"))

    @api.model_create_multi
    def create(self, vals_list):
        """Create new department records and update user's department access.

        Args:
            vals_list (list): List of dictionaries containing field values

        Returns:
            OpDepartment: Newly created department records
        """
        departments = super().create(vals_list)
        self.env.user.write({'department_ids': [(4, dept.id) for dept in departments]})
        return departments
