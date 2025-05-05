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


class OpCategory(models.Model):
    """Category model for OpenEduCat.

    This model manages categories within the institution,
    used for organizing and classifying various entities.

    Attributes:
        name (str): Name of the category
        code (str): Unique code identifier for the category
        company_id (int): Reference to the company
    """

    _name = "op.category"
    _description = "OpenEduCat Category"
    _inherit = "mail.thread"
    _order = "name"

    name = fields.Char(
        string='Name',
        size=256,
        required=True,
        tracking=True,
        help="Name of the category"
    )
    
    code = fields.Char(
        string='Code',
        size=16,
        required=True,
        tracking=True,
        help="Unique code identifier for the category"
    )
    
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,
        help="Company this category belongs to"
    )

    _sql_constraints = [
        ('unique_category_code',
         'unique(code)',
         'Code should be unique per category!')
    ]
