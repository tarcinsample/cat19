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


class OpProgram(models.Model):
    """Program model for OpenEduCat.

    This model manages academic programs within the institution,
    including their requirements and department associations.

    Attributes:
        name (str): Name of the program
        code (str): Unique code identifier for the program
        max_unit_load (float): Maximum allowed unit load
        min_unit_load (float): Minimum required unit load
        department_id (int): Reference to the department
        active (bool): Program active status
        image_1920 (binary): Program image
        program_level_id (int): Reference to the program level
    """

    _name = "op.program"
    _inherit = "mail.thread"
    _description = "OpenEduCat Program"
    _order = "name"

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        tracking=True,
        help="Name of the program"
    )
    
    code = fields.Char(
        string='Code',
        size=16,
        required=True,
        translate=True,
        tracking=True,
        help="Unique code identifier for the program"
    )
    
    max_unit_load = fields.Float(
        string="Maximum Unit Load",
        tracking=True,
        help="Maximum allowed unit load for the program"
    )
    
    min_unit_load = fields.Float(
        string="Minimum Unit Load",
        tracking=True,
        help="Minimum required unit load for the program"
    )
    
    department_id = fields.Many2one(
        comodel_name='op.department',
        string='Department',
        default=lambda self: self.env.user.dept_id.id or False,
        tracking=True,
        help="Department offering the program"
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True,
        help="Program active status"
    )
    
    image_1920 = fields.Image(
        string='Image',
        attachment=True,
        help="Program image"
    )
    
    program_level_id = fields.Many2one(
        comodel_name='op.program.level',
        string='Program Level',
        required=True,
        tracking=True,
        help="Level of the program"
    )

    _sql_constraints = [
        ('unique_code',
         'unique(code)',
         'Program code must be unique!')
    ]

    @api.constrains('max_unit_load', 'min_unit_load')
    def _check_unit_load(self):
        """Validate unit load constraints.

        Ensures that:
        - Maximum unit load is greater than minimum unit load
        - Both values are non-negative

        Raises:
            ValidationError: If unit load constraints are violated
        """
        for record in self:
            if record.max_unit_load < record.min_unit_load:
                raise ValidationError(_(
                    "Maximum unit load cannot be less than minimum unit load!"))
            if record.max_unit_load < 0 or record.min_unit_load < 0:
                raise ValidationError(_(
                    "Unit loads cannot be negative!"))


class OpProgramLevel(models.Model):
    """Program Level model for OpenEduCat.

    This model manages the different levels of academic programs
    within the institution.

    Attributes:
        name (str): Name of the program level
    """

    _name = "op.program.level"
    _inherit = "mail.thread"
    _description = "OpenEduCat Program Level"
    _order = "name"

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        tracking=True,
        help="Name of the program level"
    )

    _sql_constraints = [
        ('unique_name',
         'unique(name)',
         'Program level name must be unique!')
    ]
