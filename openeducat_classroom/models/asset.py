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


class OpAsset(models.Model):
    """Model for managing classroom assets.
    
    This model handles asset tracking and management for classrooms,
    including product details, quantities, and validation.
    """
    _name = "op.asset"
    _description = "Classroom Assets"
    _rec_name = 'display_name'

    asset_id = fields.Many2one(
        'op.classroom', 'Classroom',
        required=True,
        help="Classroom where this asset is located")
    product_id = fields.Many2one(
        'product.product', 'Product',
        required=True,
        help="Product representing this asset")
    code = fields.Char(
        'Asset Code', size=256,
        help="Unique identifier for this asset")
    product_uom_qty = fields.Float(
        'Quantity', required=True, default=1.0,
        help="Quantity of this asset in the classroom")
    display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name combining product and asset code")
    product_category_id = fields.Many2one(
        'product.category', 'Product Category',
        related='product_id.categ_id',
        store=True, readonly=True,
        help="Category of the product")
    total_value = fields.Float(
        'Total Value',
        compute='_compute_total_value',
        store=True,
        help="Total value of this asset (quantity * unit price)")

    _sql_constraints = [
        ('quantity_check',
         'CHECK (product_uom_qty > 0)',
         'Asset quantity must be greater than 0'),
        ('unique_asset_code_classroom',
         'UNIQUE(code, asset_id)',
         'Asset code must be unique per classroom'),
    ]

    @api.depends('product_id', 'code', 'product_uom_qty')
    def _compute_display_name(self):
        """Compute display name for the asset."""
        for asset in self:
            if asset.product_id:
                name = asset.product_id.name
                if asset.code:
                    name += f" [{asset.code}]"
                if asset.product_uom_qty != 1:
                    name += f" (Qty: {asset.product_uom_qty})"
                asset.display_name = name
            else:
                asset.display_name = asset.code or "Asset"

    @api.depends('product_id', 'product_uom_qty')
    def _compute_total_value(self):
        """Compute total value of the asset."""
        for asset in self:
            if asset.product_id and asset.product_uom_qty:
                asset.total_value = (
                    asset.product_id.list_price * asset.product_uom_qty
                )
            else:
                asset.total_value = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Generate asset code when product changes."""
        if self.product_id and not self.code:
            # Generate code based on product and classroom
            if self.asset_id:
                existing_assets = self.search([
                    ('product_id', '=', self.product_id.id),
                    ('asset_id', '=', self.asset_id.id)
                ])
                sequence = len(existing_assets) + 1
                self.code = f"{self.product_id.default_code or 'AST'}-{self.asset_id.code}-{sequence:03d}"

    @api.constrains('product_uom_qty')
    def _check_quantity(self):
        """Validate asset quantity."""
        for asset in self:
            if asset.product_uom_qty <= 0:
                raise ValidationError(
                    _("Asset quantity must be greater than 0.")
                )

    @api.constrains('code', 'asset_id')
    def _check_unique_code_per_classroom(self):
        """Validate unique asset code per classroom."""
        for asset in self:
            if asset.code and asset.asset_id:
                existing = self.search([
                    ('code', '=', asset.code),
                    ('asset_id', '=', asset.asset_id.id),
                    ('id', '!=', asset.id)
                ])
                if existing:
                    raise ValidationError(
                        _("Asset code '%s' already exists in classroom '%s'.")
                        % (asset.code, asset.asset_id.name)
                    )

    def name_get(self):
        """Return asset name with product and code info."""
        result = []
        for asset in self:
            if asset.product_id:
                name = asset.product_id.name
                if asset.code:
                    name += f" [{asset.code}]"
                if asset.asset_id:
                    name += f" - {asset.asset_id.name}"
            else:
                name = asset.code or f"Asset #{asset.id}"
            result.append((asset.id, name))
        return result

    def get_asset_info(self):
        """Get comprehensive asset information.
        
        Returns:
            dict: Asset information including product, location, and value
        """
        self.ensure_one()
        return {
            'name': self.display_name,
            'code': self.code,
            'product': self.product_id.name if self.product_id else None,
            'quantity': self.product_uom_qty,
            'classroom': self.asset_id.name if self.asset_id else None,
            'category': self.product_category_id.name if self.product_category_id else None,
            'value': self.total_value,
        }

    @api.model
    def create(self, vals):
        """Override create to auto-generate code if not provided."""
        if not vals.get('code') and vals.get('product_id') and vals.get('asset_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            classroom = self.env['op.classroom'].browse(vals['asset_id'])
            
            # Count existing assets of same product in classroom
            existing_count = self.search_count([
                ('product_id', '=', vals['product_id']),
                ('asset_id', '=', vals['asset_id'])
            ])
            
            sequence = existing_count + 1
            vals['code'] = f"{product.default_code or 'AST'}-{classroom.code}-{sequence:03d}"
        
        return super().create(vals)

    def unlink(self):
        """Override unlink to add validation."""
        for asset in self:
            if asset.asset_id and asset.product_uom_qty > 0:
                # Log asset removal for audit trail
                asset.asset_id.message_post(
                    body=_("Asset removed: %s (Qty: %s)") % 
                         (asset.display_name, asset.product_uom_qty)
                )
        return super().unlink()