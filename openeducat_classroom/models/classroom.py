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


class OpClassroom(models.Model):
    """Model for managing classroom information.
    
    This model handles classroom details including capacity, facilities,
    assets, and course assignments with proper validation and tracking.
    """
    _name = "op.classroom"
    _description = "Classroom"

    name = fields.Char(
        'Name', size=16, required=True,
        help="Name of the classroom")
    code = fields.Char(
        'Code', size=16, required=True,
        help="Unique code for the classroom")
    course_id = fields.Many2one(
        'op.course', 'Course',
        help="Course assigned to this classroom")
    batch_id = fields.Many2one(
        'op.batch', 'Batch',
        domain="[('course_id', '=', course_id)]",
        help="Batch assigned to this classroom")
    capacity = fields.Integer(
        string='No of Seats', required=True,
        help="Maximum number of students that can be accommodated")
    current_occupancy = fields.Integer(
        string='Current Occupancy',
        compute='_compute_current_occupancy',
        help="Current number of students assigned")
    occupancy_percentage = fields.Float(
        string='Occupancy %',
        compute='_compute_occupancy_percentage',
        help="Percentage of classroom capacity currently occupied")
    facilities = fields.One2many(
        'op.facility.line', 'classroom_id',
        string='Facility Lines',
        help="Facilities available in this classroom")
    facility_count = fields.Integer(
        string='Facility Count',
        compute='_compute_facility_count',
        help="Total number of facilities in this classroom")
    asset_line = fields.One2many(
        'op.asset', 'asset_id',
        string='Assets',
        help="Assets available in this classroom")
    asset_count = fields.Integer(
        string='Asset Count',
        compute='_compute_asset_count',
        help="Total number of assets in this classroom")
    active = fields.Boolean(
        default=True,
        help="Set to False to hide the classroom")

    _sql_constraints = [
        ('unique_classroom_code',
         'unique(code)', 'Code should be unique per classroom!'),
        ('capacity_check',
         'CHECK (capacity > 0)',
         'Classroom capacity must be greater than 0'),
        ('name_code_check',
         'CHECK (length(trim(name)) > 0 AND length(trim(code)) > 0)',
         'Classroom name and code cannot be empty')
    ]

    @api.depends('batch_id')
    def _compute_current_occupancy(self):
        """Compute current occupancy based on assigned batch."""
        for classroom in self:
            if classroom.batch_id:
                # Count students in the assigned batch
                student_count = self.env['op.student'].search_count([
                    ('course_detail_ids.batch_id', '=', classroom.batch_id.id)
                ])
                classroom.current_occupancy = student_count
            else:
                classroom.current_occupancy = 0

    @api.depends('capacity', 'current_occupancy')
    def _compute_occupancy_percentage(self):
        """Compute occupancy percentage."""
        for classroom in self:
            if classroom.capacity > 0:
                classroom.occupancy_percentage = (
                    classroom.current_occupancy / classroom.capacity
                ) * 100
            else:
                classroom.occupancy_percentage = 0

    @api.depends('facilities')
    def _compute_facility_count(self):
        """Compute total number of facilities."""
        for classroom in self:
            classroom.facility_count = len(classroom.facilities)

    @api.depends('asset_line')
    def _compute_asset_count(self):
        """Compute total number of assets."""
        for classroom in self:
            classroom.asset_count = len(classroom.asset_line)

    @api.onchange('course_id')
    def onchange_course(self):
        """Reset batch when course changes and apply domain."""
        if self.course_id:
            self.batch_id = False
            return {
                'domain': {
                    'batch_id': [('course_id', '=', self.course_id.id)]
                }
            }
        else:
            self.batch_id = False
            return {
                'domain': {
                    'batch_id': []
                }
            }

    @api.constrains('capacity', 'current_occupancy')
    def _check_capacity_assignment(self):
        """Validate that current occupancy doesn't exceed capacity."""
        for classroom in self:
            if classroom.current_occupancy > classroom.capacity:
                raise ValidationError(
                    _("Current occupancy (%d) cannot exceed classroom capacity (%d) "
                      "for classroom '%s'.")
                    % (classroom.current_occupancy, classroom.capacity, classroom.name)
                )

    @api.constrains('batch_id', 'course_id')
    def _check_batch_course_consistency(self):
        """Validate that batch belongs to the assigned course."""
        for classroom in self:
            if classroom.batch_id and classroom.course_id:
                if classroom.batch_id.course_id != classroom.course_id:
                    raise ValidationError(
                        _("Batch '%s' does not belong to course '%s'. "
                          "Please select a batch from the assigned course.")
                        % (classroom.batch_id.name, classroom.course_id.name)
                    )

    def name_get(self):
        """Return classroom name with code and capacity info."""
        result = []
        for classroom in self:
            name = f"{classroom.name} ({classroom.code})"
            if classroom.capacity:
                name += f" - Capacity: {classroom.capacity}"
            result.append((classroom.id, name))
        return result

    def get_available_capacity(self):
        """Get available capacity for the classroom.
        
        Returns:
            int: Number of available seats in the classroom
        """
        self.ensure_one()
        return max(0, self.capacity - self.current_occupancy)

    def is_capacity_available(self, required_seats=1):
        """Check if classroom has available capacity.
        
        Args:
            required_seats (int): Number of seats required
            
        Returns:
            bool: True if classroom can accommodate required seats
        """
        self.ensure_one()
        return self.get_available_capacity() >= required_seats

    def validate_assignment(self, student_count=1):
        """Validate if students can be assigned to this classroom.
        
        Args:
            student_count (int): Number of students to assign
            
        Raises:
            ValidationError: If assignment would exceed capacity
        """
        self.ensure_one()
        if not self.is_capacity_available(student_count):
            raise ValidationError(
                _("Cannot assign %d students to classroom '%s'. "
                  "Available capacity: %d seats.")
                % (student_count, self.name, self.get_available_capacity())
            )