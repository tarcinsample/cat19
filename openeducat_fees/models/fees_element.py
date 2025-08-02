##############################################################################
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
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpFeesElementLine(models.Model):
    """Model for managing individual fee elements within payment terms.
    
    This model handles specific fee components like tuition, library,
    lab fees, etc., with percentage-based allocation within payment terms.
    """
    _name = "op.fees.element"
    _description = "Fees Element for course"
    _rec_name = "display_name"
    _order = "sequence, product_id"

    sequence = fields.Integer(
        'Sequence', default=10,
        help="Sequence order for fee element display")
    product_id = fields.Many2one(
        'product.product', 'Product(s)', 
        required=True, 
        domain="[('can_be_expensed', '=', False)]",
        help="Product representing this fee component")
    value = fields.Float(
        'Value (%)', required=True,
        help="Percentage of line amount for this element")
    fees_terms_line_id = fields.Many2one(
        'op.fees.terms.line', 'Fees Terms',
        required=True, ondelete='cascade',
        help="Parent fee terms line")
    display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name with product and percentage")
    amount_estimate = fields.Monetary(
        'Estimated Amount',
        compute='_compute_amount_estimate',
        currency_field='currency_id',
        help="Estimated amount based on product price")
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        related='fees_terms_line_id.fees_id.company_id.currency_id',
        readonly=True,
        help="Currency for calculations")
    active = fields.Boolean(
        'Active', default=True,
        help="Set to False to hide this fee element")

    _sql_constraints = [
        ('value_positive', 
         'CHECK (value > 0 AND value <= 100)', 
         'Element percentage must be between 0 and 100'),
        ('sequence_positive', 
         'CHECK (sequence > 0)', 
         'Sequence must be positive')
    ]

    @api.depends('product_id', 'value')
    def _compute_display_name(self):
        """Compute display name showing product and percentage."""
        for element in self:
            if element.product_id:
                name = f"{element.product_id.name} ({element.value}%)"
            else:
                name = f"Fee Element ({element.value}%)"
            element.display_name = name

    @api.depends('product_id', 'value')
    def _compute_amount_estimate(self):
        """Compute estimated amount based on product price."""
        for element in self:
            if element.product_id and element.value:
                element.amount_estimate = (
                    element.product_id.list_price * element.value / 100
                )
            else:
                element.amount_estimate = 0.0

    @api.constrains('value')
    def _check_value_range(self):
        """Validate percentage value range."""
        for element in self:
            if element.value <= 0 or element.value > 100:
                raise ValidationError(
                    _("Fee element percentage must be between 0 and 100. "
                      "Current value: %s") % element.value
                )

    @api.constrains('product_id')
    def _check_product_validity(self):
        """Validate product for fee usage."""
        for element in self:
            if element.product_id:
                if element.product_id.type != 'service':
                    raise ValidationError(
                        _("Fee element product '%s' must be a service type.")
                        % element.product_id.name
                    )
                if not element.product_id.active:
                    raise ValidationError(
                        _("Cannot use inactive product '%s' for fee element.")
                        % element.product_id.name
                    )

    @api.constrains('fees_terms_line_id', 'product_id')
    def _check_element_uniqueness(self):
        """Ensure no duplicate elements in same fee term line."""
        for element in self:
            if element.fees_terms_line_id and element.product_id:
                existing = self.search([
                    ('fees_terms_line_id', '=', element.fees_terms_line_id.id),
                    ('product_id', '=', element.product_id.id),
                    ('id', '!=', element.id)
                ])
                if existing:
                    raise ValidationError(
                        _("Product '%s' already exists in this fee term line. "
                          "Please choose a different product.") 
                        % element.product_id.name
                    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update value based on product configuration."""
        if self.product_id:
            # Set default value if product has a specific fee percentage
            if hasattr(self.product_id, 'default_fee_percentage'):
                self.value = self.product_id.default_fee_percentage
            
            # Warning for non-service products
            if self.product_id.type != 'service':
                return {
                    'warning': {
                        'title': _('Product Type Warning'),
                        'message': _('It is recommended to use service type '
                                   'products for fee elements.')
                    }
                }

    def calculate_element_amount(self, base_amount):
        """Calculate element amount for given base amount.
        
        Args:
            base_amount (float): Base amount to calculate percentage from
            
        Returns:
            float: Calculated element amount
        """
        self.ensure_one()
        return (base_amount * self.value) / 100

    def get_element_details(self):
        """Get detailed information about the fee element.
        
        Returns:
            dict: Element details including product info and calculations
        """
        self.ensure_one()
        return {
            'product_name': self.product_id.name,
            'product_code': self.product_id.default_code or '',
            'percentage': self.value,
            'estimated_amount': self.amount_estimate,
            'currency': self.currency_id.name,
            'sequence': self.sequence,
            'category': self.product_id.categ_id.name
        }

    @api.model
    def get_elements_by_category(self, fees_terms_line_id):
        """Get fee elements grouped by product category.
        
        Args:
            fees_terms_line_id (int): Fee terms line ID
            
        Returns:
            dict: Elements grouped by category
        """
        elements = self.search([
            ('fees_terms_line_id', '=', fees_terms_line_id),
            ('active', '=', True)
        ], order='sequence, product_id')
        
        categories = {}
        for element in elements:
            category = element.product_id.categ_id.name
            if category not in categories:
                categories[category] = []
            categories[category].append(element.get_element_details())
        
        return categories

    def validate_element_configuration(self):
        """Validate the complete fee element configuration.
        
        Returns:
            dict: Validation result with status and messages
        """
        self.ensure_one()
        errors = []
        warnings = []
        
        # Check product configuration
        if not self.product_id.list_price:
            warnings.append(_("Product '%s' has no list price set.") 
                          % self.product_id.name)
        
        # Check percentage validity
        if self.value <= 0:
            errors.append(_("Element percentage must be greater than 0."))
        
        # Check product category
        if not self.product_id.categ_id:
            warnings.append(_("Product '%s' has no category assigned.") 
                          % self.product_id.name)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }