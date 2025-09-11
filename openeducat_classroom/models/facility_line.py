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
    """Extended facility line model for classroom integration.
    
    This model extends the base facility line to add classroom-specific
    functionality and validation for facility management.
    """
    _inherit = "op.facility.line"

    classroom_id = fields.Many2one(
        'op.classroom', 'Classroom',
        help="Classroom where this facility is located")
    facility_status = fields.Selection([
        ('available', 'Available'),
        ('maintenance', 'Under Maintenance'),
        ('damaged', 'Damaged'),
        ('reserved', 'Reserved')
    ], string='Status', default='available',
        help="Current status of the facility")
    last_maintenance_date = fields.Date(
        string='Last Maintenance',
        help="Date of last maintenance performed")
    next_maintenance_date = fields.Date(
        string='Next Maintenance',
        help="Scheduled date for next maintenance")
    maintenance_notes = fields.Text(
        string='Maintenance Notes',
        help="Notes about facility condition and maintenance history")

    _sql_constraints = [
        ('unique_facility_classroom',
         'UNIQUE(facility_id, classroom_id)',
         'Facility already exists in this classroom. Please update the quantity instead.'),
        ('maintenance_date_check',
         'CHECK (next_maintenance_date IS NULL OR next_maintenance_date >= last_maintenance_date)',
         'Next maintenance date must be after the last maintenance date.')
    ]

    @api.constrains('last_maintenance_date', 'next_maintenance_date')
    def _check_maintenance_dates(self):
        """Validate maintenance date consistency."""
        for line in self:
            if (line.last_maintenance_date and line.next_maintenance_date and
                line.next_maintenance_date < line.last_maintenance_date):
                raise ValidationError(
                    _("Next maintenance date cannot be before the last maintenance date "
                      "for facility '%s' in classroom '%s'.")
                    % (line.facility_id.name, line.classroom_id.name if line.classroom_id else 'Unknown')
                )

    @api.constrains('facility_status', 'quantity')
    def _check_facility_availability(self):
        """Validate facility availability based on status."""
        for line in self:
            if line.facility_status in ['damaged', 'maintenance'] and line.quantity > 0:
                # Warning: facility is not available but quantity is positive
                if line.classroom_id:
                    line.classroom_id.message_post(
                        body=_("Warning: Facility '%s' is marked as '%s' but quantity is %s. "
                               "Consider updating the status or quantity.")
                        % (line.facility_id.name, line.facility_status, line.quantity)
                    )

    @api.onchange('facility_status')
    def _onchange_facility_status(self):
        """Update maintenance dates based on status change."""
        if self.facility_status == 'maintenance':
            if not self.last_maintenance_date:
                self.last_maintenance_date = fields.Date.today()
        elif self.facility_status == 'available':
            if self.last_maintenance_date and not self.next_maintenance_date:
                # Set next maintenance 6 months from now by default
                self.next_maintenance_date = fields.Date.add(
                    fields.Date.today(), months=6
                )

    def name_get(self):
        """Return facility line name with classroom and status info."""
        result = []
        for line in self:
            name = line.facility_id.name if line.facility_id else "Facility"
            if line.classroom_id:
                name += f" - {line.classroom_id.name}"
            if line.quantity > 1:
                name += f" (Qty: {line.quantity})"
            if line.facility_status != 'available':
                name += f" [{line.facility_status.title()}]"
            result.append((line.id, name))
        return result

    def get_facility_info(self):
        """Get comprehensive facility information.
        
        Returns:
            dict: Facility information including status and maintenance
        """
        self.ensure_one()
        return {
            'facility': self.facility_id.name if self.facility_id else None,
            'classroom': self.classroom_id.name if self.classroom_id else None,
            'quantity': self.quantity,
            'status': self.facility_status,
            'last_maintenance': self.last_maintenance_date,
            'next_maintenance': self.next_maintenance_date,
            'notes': self.maintenance_notes,
            'available_quantity': self.quantity if self.facility_status == 'available' else 0,
        }

    def set_maintenance_mode(self, notes=None):
        """Set facility to maintenance mode.
        
        Args:
            notes (str): Optional maintenance notes
        """
        self.ensure_one()
        vals = {
            'facility_status': 'maintenance',
            'last_maintenance_date': fields.Date.today(),
        }
        if notes:
            vals['maintenance_notes'] = notes
        self.write(vals)
        
        if self.classroom_id:
            self.classroom_id.message_post(
                body=_("Facility '%s' has been set to maintenance mode.") 
                     % self.facility_id.name
            )

    def complete_maintenance(self, next_maintenance_months=6):
        """Complete maintenance and set next maintenance date.
        
        Args:
            next_maintenance_months (int): Months until next maintenance
        """
        self.ensure_one()
        self.write({
            'facility_status': 'available',
            'next_maintenance_date': fields.Date.add(
                fields.Date.today(), months=next_maintenance_months
            ),
        })
        
        if self.classroom_id:
            self.classroom_id.message_post(
                body=_("Maintenance completed for facility '%s'. Next maintenance: %s") 
                     % (self.facility_id.name, self.next_maintenance_date)
            )

    def mark_as_damaged(self, notes=None):
        """Mark facility as damaged.
        
        Args:
            notes (str): Optional damage notes
        """
        self.ensure_one()
        vals = {'facility_status': 'damaged'}
        if notes:
            vals['maintenance_notes'] = notes
        self.write(vals)
        
        if self.classroom_id:
            self.classroom_id.message_post(
                body=_("Facility '%s' has been marked as damaged.") 
                     % self.facility_id.name
            )

    def get_available_quantity(self):
        """Get available quantity based on facility status.
        
        Returns:
            float: Available quantity for use
        """
        self.ensure_one()
        if self.facility_status == 'available':
            return self.quantity
        return 0.0

    @api.model
    def get_classroom_facility_summary(self, classroom_id):
        """Get facility summary for a classroom.
        
        Args:
            classroom_id (int): ID of the classroom
            
        Returns:
            dict: Summary of facilities by status
        """
        facilities = self.search([('classroom_id', '=', classroom_id)])
        summary = {
            'total_facilities': len(facilities),
            'available': 0,
            'maintenance': 0,
            'damaged': 0,
            'reserved': 0,
            'total_quantity': 0,
            'available_quantity': 0,
        }
        
        for facility in facilities:
            summary[facility.facility_status] += 1
            summary['total_quantity'] += facility.quantity
            if facility.facility_status == 'available':
                summary['available_quantity'] += facility.quantity
                
        return summary