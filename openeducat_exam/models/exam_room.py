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

from functools import lru_cache

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class OpExamRoom(models.Model):
    _name = "op.exam.room"
    _description = "Exam Room"
    _rec_name = "name"

    name = fields.Char('Name', size=256, required=True,
                       help="Name of the exam room")
    classroom_id = fields.Many2one('op.classroom', 'Classroom', required=True,
                                   help="Associated classroom for this exam room")
    capacity = fields.Integer('No of Seats', 
                              help="Maximum number of students that can be seated")
    active = fields.Boolean(default=True)
    allocated_count = fields.Integer('Allocated Students', 
                                     compute='_compute_allocated_count',
                                     help="Number of students currently allocated to this room")
    available_seats = fields.Integer('Available Seats',
                                     compute='_compute_available_seats',
                                     help="Number of available seats in this room")

    @api.depends('capacity')
    def _compute_allocated_count(self):
        """Compute number of students allocated to this room.
        
        Counts current exam attendees assigned to this room.
        """
        for record in self:
            # Count students allocated to this room across all active exams
            allocated = self.env['op.exam.attendees'].search_count([
                ('room_id', '=', record.id),
                ('exam_id.state', 'in', ['schedule', 'held'])
            ])
            record.allocated_count = allocated
    
    @api.depends('capacity', 'allocated_count')
    def _compute_available_seats(self):
        """Compute available seats in the room.
        
        Calculates remaining capacity after current allocations.
        """
        for record in self:
            record.available_seats = max(0, record.capacity - record.allocated_count)

    @api.constrains('capacity', 'classroom_id')
    def _check_capacity(self):
        """Validate exam room capacity constraints.
        
        Raises:
            ValidationError: If capacity is invalid or exceeds classroom capacity
        """
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_(
                    "Exam room capacity cannot be negative."))
            if record.classroom_id and record.capacity > record.classroom_id.capacity:
                raise ValidationError(_(
                    "Exam room capacity (%d) cannot exceed classroom capacity (%d).") % (
                    record.capacity, record.classroom_id.capacity))

    @api.onchange('classroom_id')
    def onchange_classroom(self):
        """Update capacity when classroom changes."""
        if self.classroom_id:
            self.capacity = self.classroom_id.capacity
        else:
            self.capacity = 0
            
    @tools.ormcache('self.id', 'exam_id', 'student_count')
    def check_availability(self, exam_id, student_count=1):
        """Check if room has sufficient capacity for exam with caching.
        
        Args:
            exam_id: ID of the exam to check availability for
            student_count: Number of students to accommodate
            
        Returns:
            bool: True if room has sufficient capacity
        """
        self.ensure_one()
        
        # Check room capacity
        if student_count > self.capacity:
            return False
            
        # Check current allocations for the specific exam time
        exam = self.env['op.exam'].browse(exam_id)
        if not exam.exists():
            return False
            
        # Find overlapping exams in this room
        overlapping_exams = self.env['op.exam'].search([
            ('id', '!=', exam.id),
            ('state', 'in', ['schedule', 'held']),
            ('start_time', '<', exam.end_time),
            ('end_time', '>', exam.start_time)
        ])
        
        # Count students already allocated to this room during overlapping time
        conflicting_allocations = self.env['op.exam.attendees'].search_count([
            ('room_id', '=', self.id),
            ('exam_id', 'in', overlapping_exams.ids)
        ])
        
        available_capacity = self.capacity - conflicting_allocations
        return student_count <= available_capacity
