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


class OpFacilityLine(models.Model):
    """Base model for managing facility allocations.
    
    This model handles the allocation of facilities to various locations
    with quantity tracking, availability management, and usage validation.
    """
    _name = "op.facility.line"
    _rec_name = "display_name"
    _description = "Manage Facility Line"
    _order = "facility_id, quantity desc"

    facility_id = fields.Many2one(
        'op.facility', 'Facility',
        required=True,
        help="Facility being allocated")
    quantity = fields.Float(
        'Quantity', required=True, default=1.0,
        help="Quantity of the facility allocated")
    display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name for the facility line")
    allocation_date = fields.Date(
        'Allocation Date',
        default=fields.Date.today,
        help="Date when the facility was allocated")
    notes = fields.Text(
        'Notes',
        help="Additional notes about the allocation")
    active = fields.Boolean(
        default=True,
        help="Set to False to hide the facility line")

    _sql_constraints = [
        ('quantity_positive',
         'CHECK (quantity > 0)',
         'Facility quantity must be greater than 0'),
    ]

    @api.depends('facility_id', 'quantity')
    def _compute_display_name(self):
        """Compute display name for the facility line."""
        for line in self:
            if line.facility_id:
                name = line.facility_id.name
                if line.quantity != 1:
                    name += f" (Qty: {line.quantity})"
                line.display_name = name
            else:
                line.display_name = f"Facility Line #{line.id}"

    @api.constrains('quantity')
    def check_quantity(self):
        """Validate facility quantity."""
        for record in self:
            if record.quantity <= 0.0:
                raise ValidationError(
                    _("Facility quantity must be greater than 0. "
                      "Current value: %s") % record.quantity
                )

    @api.constrains('facility_id')
    def _check_facility_active(self):
        """Validate that facility is active."""
        for line in self:
            if line.facility_id and not line.facility_id.active:
                raise ValidationError(
                    _("Cannot allocate inactive facility '%s'. "
                      "Please activate the facility first.")
                    % line.facility_id.name
                )

    @api.onchange('facility_id')
    def _onchange_facility_id(self):
        """Set default quantity when facility changes."""
        if self.facility_id and self.facility_id.standard_quantity:
            self.quantity = self.facility_id.standard_quantity

    def name_get(self):
        """Return facility line name with facility and quantity info."""
        result = []
        for line in self:
            if line.facility_id:
                name = f"{line.facility_id.name}"
                if line.quantity > 1:
                    name += f" (Qty: {line.quantity})"
                if hasattr(line, 'classroom_id') and line.classroom_id:
                    name += f" - {line.classroom_id.name}"
            else:
                name = f"Facility Line #{line.id}"
            result.append((line.id, name))
        return result

    def get_allocation_info(self):
        """Get comprehensive allocation information.
        
        Returns:
            dict: Allocation information including facility details
        """
        self.ensure_one()
        return {
            'facility': self.facility_id.name if self.facility_id else None,
            'facility_code': self.facility_id.code if self.facility_id else None,
            'facility_type': self.facility_id.facility_type if self.facility_id else None,
            'quantity': self.quantity,
            'allocation_date': self.allocation_date,
            'notes': self.notes,
            'active': self.active,
        }

    def update_quantity(self, new_quantity, notes=None):
        """Update facility quantity with validation.
        
        Args:
            new_quantity (float): New quantity to set
            notes (str): Optional notes about the change
        """
        self.ensure_one()
        if new_quantity <= 0:
            raise ValidationError(
                _("New quantity must be greater than 0.")
            )
        
        old_quantity = self.quantity
        self.quantity = new_quantity
        
        # Add notes about the change
        change_note = f"Quantity changed from {old_quantity} to {new_quantity}"
        if notes:
            change_note += f". Notes: {notes}"
        
        if self.notes:
            self.notes += f"\n{change_note}"
        else:
            self.notes = change_note

    def transfer_to_location(self, new_location_field, new_location_id, quantity=None):
        """Transfer facility to a different location.
        
        Args:
            new_location_field (str): Field name for the new location
            new_location_id (int): ID of the new location
            quantity (float): Quantity to transfer (None for all)
        """
        self.ensure_one()
        
        transfer_qty = quantity or self.quantity
        if transfer_qty <= 0 or transfer_qty > self.quantity:
            raise ValidationError(
                _("Invalid transfer quantity. Must be between 0 and %s.")
                % self.quantity
            )
        
        # Create new allocation at destination
        new_vals = {
            'facility_id': self.facility_id.id,
            'quantity': transfer_qty,
            'allocation_date': fields.Date.today(),
            'notes': f"Transferred from {self.display_name}",
        }
        new_vals[new_location_field] = new_location_id
        
        self.env['op.facility.line'].create(new_vals)
        
        # Update or remove source allocation
        if transfer_qty >= self.quantity:
            self.unlink()
        else:
            self.quantity -= transfer_qty
            self.notes = (self.notes or '') + f"\n{transfer_qty} units transferred"

    @api.model
    def create(self, vals):
        """Override create to add allocation tracking."""
        line = super().create(vals)
        
        # Log allocation creation
        if line.facility_id:
            line.facility_id.message_post(
                body=_("Facility allocated: %s units to %s") %
                     (line.quantity, line.display_name)
            )
        
        return line

    def write(self, vals):
        """Override write to track quantity changes."""
        for line in self:
            old_quantity = line.quantity
            
        result = super().write(vals)
        
        # Log quantity changes
        if 'quantity' in vals:
            for line in self:
                if line.quantity != old_quantity:
                    line.facility_id.message_post(
                        body=_("Quantity updated: from %s to %s units for %s") %
                             (old_quantity, line.quantity, line.display_name)
                    )
        
        return result

    def unlink(self):
        """Override unlink to log allocation removal."""
        for line in self:
            if line.facility_id:
                line.facility_id.message_post(
                    body=_("Facility allocation removed: %s units from %s") %
                         (line.quantity, line.display_name)
                )
        
        return super().unlink()

    @api.model
    def get_allocation_summary_by_facility(self, facility_ids=None):
        """Get allocation summary grouped by facility.
        
        Args:
            facility_ids (list): List of facility IDs to include
            
        Returns:
            dict: Summary data grouped by facility
        """
        domain = [('active', '=', True)]
        if facility_ids:
            domain.append(('facility_id', 'in', facility_ids))
        
        lines = self.search(domain)
        summary = {}
        
        for line in lines:
            facility_id = line.facility_id.id
            if facility_id not in summary:
                summary[facility_id] = {
                    'facility_name': line.facility_id.name,
                    'facility_code': line.facility_id.code,
                    'total_quantity': 0,
                    'allocation_count': 0,
                    'locations': [],
                }
            
            summary[facility_id]['total_quantity'] += line.quantity
            summary[facility_id]['allocation_count'] += 1
            
            location_info = {
                'line_id': line.id,
                'quantity': line.quantity,
                'allocation_date': line.allocation_date,
            }
            
            # Add location-specific info if available
            if hasattr(line, 'classroom_id') and line.classroom_id:
                location_info['classroom'] = line.classroom_id.name
            
            summary[facility_id]['locations'].append(location_info)
        
        return summary

    @api.model
    def optimize_allocations(self, facility_id, min_quantity_threshold=0.1):
        """Optimize facility allocations by consolidating small quantities.
        
        Args:
            facility_id (int): ID of the facility to optimize
            min_quantity_threshold (float): Minimum quantity threshold
            
        Returns:
            dict: Summary of optimization actions
        """
        lines = self.search([
            ('facility_id', '=', facility_id),
            ('quantity', '<', min_quantity_threshold),
            ('active', '=', True)
        ])
        
        optimization_summary = {
            'removed_lines': 0,
            'consolidated_quantity': 0,
            'actions': []
        }
        
        for line in lines:
            optimization_summary['removed_lines'] += 1
            optimization_summary['consolidated_quantity'] += line.quantity
            optimization_summary['actions'].append(
                f"Removed small allocation: {line.quantity} from {line.display_name}"
            )
            line.unlink()
        
        return optimization_summary