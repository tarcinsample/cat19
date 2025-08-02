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


class OpFacility(models.Model):
    """Model for managing educational facilities.
    
    This model handles facility information including types, availability,
    allocation tracking, and usage statistics across classrooms and departments.
    """
    _name = "op.facility"
    _description = "Manage Facility"
    _order = "name, code"

    name = fields.Char(
        'Name', size=16, required=True,
        help="Name of the facility")
    code = fields.Char(
        'Code', size=16, required=True,
        help="Unique code for the facility")
    description = fields.Text(
        'Description',
        help="Detailed description of the facility")
    facility_type = fields.Selection([
        ('furniture', 'Furniture'),
        ('equipment', 'Equipment'),
        ('technology', 'Technology'),
        ('safety', 'Safety Equipment'),
        ('sports', 'Sports Equipment'),
        ('laboratory', 'Laboratory Equipment'),
        ('library', 'Library Resources'),
        ('maintenance', 'Maintenance Tools'),
        ('other', 'Other')
    ], string='Type', default='other',
        help="Type/category of the facility")
    unit_of_measure = fields.Char(
        'Unit of Measure', size=10, default='Unit',
        help="Unit of measurement for this facility")
    standard_quantity = fields.Float(
        'Standard Quantity', default=1.0,
        help="Standard quantity typically allocated per location")
    total_allocated = fields.Integer(
        'Total Allocated',
        compute='_compute_allocation_stats',
        help="Total quantity allocated across all locations")
    total_available = fields.Integer(
        'Total Available',
        compute='_compute_allocation_stats',
        help="Total quantity available across all locations")
    usage_percentage = fields.Float(
        'Usage %',
        compute='_compute_allocation_stats',
        help="Percentage of facilities currently in use")
    allocation_count = fields.Integer(
        'Allocation Count',
        compute='_compute_allocation_count',
        help="Number of locations where this facility is allocated")
    maintenance_required = fields.Boolean(
        'Maintenance Required',
        compute='_compute_maintenance_status',
        help="True if any allocation requires maintenance")
    active = fields.Boolean(
        default=True,
        help="Set to False to hide the facility")

    _sql_constraints = [
        ('unique_facility_code',
         'unique(code)', 'Code should be unique per facility!'),
        ('name_code_check',
         'CHECK (length(trim(name)) > 0 AND length(trim(code)) > 0)',
         'Facility name and code cannot be empty'),
        ('standard_quantity_check',
         'CHECK (standard_quantity >= 0)',
         'Standard quantity must be non-negative')
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Compute display name for the facility."""
        for facility in self:
            facility.display_name = f"{facility.name} [{facility.code}]"

    @api.depends()
    def _compute_allocation_stats(self):
        """Compute allocation statistics for the facility."""
        for facility in self:
            facility_lines = self.env['op.facility.line'].search([
                ('facility_id', '=', facility.id)
            ])
            
            total_allocated = sum(line.quantity for line in facility_lines)
            available_lines = facility_lines.filtered(
                lambda l: hasattr(l, 'facility_status') and l.facility_status == 'available'
            )
            total_available = sum(line.quantity for line in available_lines)
            
            facility.total_allocated = total_allocated
            facility.total_available = total_available
            
            if total_allocated > 0:
                facility.usage_percentage = (total_available / total_allocated) * 100
            else:
                facility.usage_percentage = 0

    @api.depends()
    def _compute_allocation_count(self):
        """Compute number of allocations for this facility."""
        for facility in self:
            facility.allocation_count = self.env['op.facility.line'].search_count([
                ('facility_id', '=', facility.id)
            ])

    @api.depends()
    def _compute_maintenance_status(self):
        """Compute if facility requires maintenance."""
        for facility in self:
            maintenance_lines = self.env['op.facility.line'].search([
                ('facility_id', '=', facility.id),
                ('facility_status', 'in', ['maintenance', 'damaged'])
            ])
            facility.maintenance_required = bool(maintenance_lines)

    def name_get(self):
        """Return facility name with code and type info."""
        result = []
        for facility in self:
            name = f"{facility.name} [{facility.code}]"
            if facility.facility_type != 'other':
                name += f" - {facility.facility_type.title()}"
            if facility.total_allocated:
                name += f" (Allocated: {facility.total_allocated})"
            result.append((facility.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search including code and description."""
        args = args or []
        if name:
            domain = [
                '|', '|',
                ('name', operator, name),
                ('code', operator, name),
                ('description', operator, name)
            ]
            facilities = self.search(domain + args, limit=limit)
            return facilities.name_get()
        return super().name_search(name, args, operator, limit)

    def get_facility_summary(self):
        """Get comprehensive facility summary.
        
        Returns:
            dict: Facility summary including allocations and status
        """
        self.ensure_one()
        facility_lines = self.env['op.facility.line'].search([
            ('facility_id', '=', self.id)
        ])
        
        classroom_count = len(facility_lines.mapped('classroom_id'))
        
        # Count by status if facility_status field exists
        status_counts = {}
        if facility_lines and hasattr(facility_lines[0], 'facility_status'):
            for status in ['available', 'maintenance', 'damaged', 'reserved']:
                status_counts[status] = len(facility_lines.filtered(
                    lambda l: l.facility_status == status
                ))
        
        return {
            'name': self.name,
            'code': self.code,
            'type': self.facility_type,
            'total_allocated': self.total_allocated,
            'total_available': self.total_available,
            'usage_percentage': self.usage_percentage,
            'allocation_count': self.allocation_count,
            'classroom_count': classroom_count,
            'maintenance_required': self.maintenance_required,
            'status_breakdown': status_counts,
        }

    def get_available_quantity(self, location_type='classroom', location_id=None):
        """Get available quantity for a specific location.
        
        Args:
            location_type (str): Type of location (classroom, department, etc.)
            location_id (int): ID of the location
            
        Returns:
            float: Available quantity at the location
        """
        self.ensure_one()
        domain = [('facility_id', '=', self.id)]
        
        if location_type == 'classroom' and location_id:
            domain.append(('classroom_id', '=', location_id))
        
        facility_lines = self.env['op.facility.line'].search(domain)
        
        # Filter by availability if status field exists
        available_lines = facility_lines
        if facility_lines and hasattr(facility_lines[0], 'facility_status'):
            available_lines = facility_lines.filtered(
                lambda l: l.facility_status == 'available'
            )
        
        return sum(line.quantity for line in available_lines)

    def allocate_to_classroom(self, classroom_id, quantity, notes=None):
        """Allocate facility to a classroom.
        
        Args:
            classroom_id (int): ID of the classroom
            quantity (float): Quantity to allocate
            notes (str): Optional allocation notes
            
        Returns:
            recordset: Created facility line
        """
        self.ensure_one()
        
        # Check if allocation already exists
        existing = self.env['op.facility.line'].search([
            ('facility_id', '=', self.id),
            ('classroom_id', '=', classroom_id)
        ])
        
        if existing:
            # Update existing allocation
            existing.quantity += quantity
            if notes:
                existing.maintenance_notes = (existing.maintenance_notes or '') + '\n' + notes
            return existing
        else:
            # Create new allocation
            vals = {
                'facility_id': self.id,
                'classroom_id': classroom_id,
                'quantity': quantity,
            }
            if notes:
                vals['maintenance_notes'] = notes
            return self.env['op.facility.line'].create(vals)

    def deallocate_from_classroom(self, classroom_id, quantity=None):
        """Deallocate facility from a classroom.
        
        Args:
            classroom_id (int): ID of the classroom
            quantity (float): Quantity to deallocate (None for all)
        """
        self.ensure_one()
        
        allocation = self.env['op.facility.line'].search([
            ('facility_id', '=', self.id),
            ('classroom_id', '=', classroom_id)
        ])
        
        if allocation:
            if quantity is None or quantity >= allocation.quantity:
                allocation.unlink()
            else:
                allocation.quantity -= quantity

    @api.model
    def get_facility_allocation_report(self, facility_type=None):
        """Generate facility allocation report.
        
        Args:
            facility_type (str): Filter by facility type
            
        Returns:
            list: Report data with allocation statistics
        """
        domain = [('active', '=', True)]
        if facility_type:
            domain.append(('facility_type', '=', facility_type))
        
        facilities = self.search(domain)
        report_data = []
        
        for facility in facilities:
            summary = facility.get_facility_summary()
            report_data.append(summary)
        
        return report_data

    @api.constrains('standard_quantity')
    def _check_standard_quantity(self):
        """Validate standard quantity."""
        for facility in self:
            if facility.standard_quantity < 0:
                raise ValidationError(
                    _("Standard quantity for facility '%s' cannot be negative.")
                    % facility.name
                )

    def action_view_allocations(self):
        """Open allocation view for this facility."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Allocations for {self.name}',
            'res_model': 'op.facility.line',
            'view_mode': 'tree,form',
            'domain': [('facility_id', '=', self.id)],
            'context': {'default_facility_id': self.id},
        }