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


class OpAsset(models.Model):
    """
    Classroom Asset Model
    
    This model manages the assets assigned to classrooms. It tracks
    the products, quantities, and codes associated with classroom assets.
    """
    _name = "op.asset"
    _description = "Classroom Assets"
    _order = "code"

    # Relationships
    asset_id = fields.Many2one(
        'op.classroom',
        string='Asset',
        help="The classroom this asset is assigned to"
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        help="The product representing this asset"
    )

    # Asset Information
    code = fields.Char(
        string='Code',
        size=256,
        help="Unique identifier code for the asset"
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        help="Quantity of the asset"
    )
