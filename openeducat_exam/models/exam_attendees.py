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


class OpExamAttendees(models.Model):
    _name = "op.exam.attendees"
    _rec_name = "student_id"
    _description = "Exam Attendees"

    student_id = fields.Many2one('op.student', 'Student', required=True)
    status = fields.Selection(
        [('present', 'Present'), ('absent', 'Absent')],
        'Status', default="present", required=True)
    marks = fields.Integer('Marks')
    note = fields.Text('Note')
    exam_id = fields.Many2one(
        'op.exam', 'Exam', required=True, ondelete="cascade")
    course_id = fields.Many2one('op.course', 'Course',
                                compute='_compute_exam_details',
                                store=True, readonly=True)
    batch_id = fields.Many2one('op.batch', 'Batch',
                               compute='_compute_exam_details',
                               store=True, readonly=True)
    room_id = fields.Many2one('op.exam.room', 'Room')

    _sql_constraints = [
        ('unique_attendees',
         'unique(student_id,exam_id)',
         'Attendee must be unique per exam.'),
    ]

    @api.constrains('marks', 'exam_id')
    def _check_marks_range(self):
        """Validate marks are within exam total marks range.
        
        Raises:
            ValidationError: If marks are outside valid range
        """
        for record in self:
            if record.status == 'present' and record.marks is not None:
                if record.exam_id and record.marks < 0:
                    raise ValidationError(_(
                        "Marks cannot be negative for student '%s'.") % 
                        record.student_id.name)
                if record.exam_id and record.marks > record.exam_id.total_marks:
                    raise ValidationError(_(
                        "Marks (%d) cannot exceed total marks (%d) for student '%s'.") % (
                        record.marks, record.exam_id.total_marks, record.student_id.name))

    @api.onchange('marks')
    def _onchange_marks(self):
        """Update exam results_entered status when marks change."""
        if self.exam_id:
            # Check if any marks are entered for present students
            present_attendees = self.exam_id.attendees_line.filtered(lambda a: a.status == 'present')
            has_marks = any(attendee.marks not in (None, False) for attendee in present_attendees)
            self.exam_id.results_entered = has_marks

    @api.depends('exam_id')
    def _compute_exam_details(self):
        for record in self:
            if record.exam_id:
                record.course_id = record.exam_id.session_id.course_id.id
                record.batch_id = record.exam_id.session_id.batch_id.id
            else:
                record.course_id = False
                record.batch_id = False

    @api.onchange('exam_id')
    def onchange_exam(self):
        """Update course and batch when exam changes."""
        if self.exam_id:
            self.course_id = self.exam_id.course_id.id
            self.batch_id = self.exam_id.batch_id.id
            
            # Return domain to filter students by course and batch
            return {
                'domain': {
                    'student_id': [
                        ('course_detail_ids.course_id', '=', self.course_id.id),
                        ('course_detail_ids.batch_id', '=', self.batch_id.id),
                        ('active', '=', True)
                    ]
                }
            }
        else:
            self.course_id = False
            self.batch_id = False
            self.student_id = False
            
            return {
                'domain': {
                    'student_id': []
                }
            }

    @api.onchange('status')
    def _onchange_status(self):
        """Update marks when attendance status changes."""
        if self.status == 'absent':
            self.marks = 0
        elif self.status == 'present' and self.marks == 0:
            self.marks = None  # Clear marks for present students
            
    def compute_grade(self):
        """Compute grade based on marks and exam configuration.
        
        Returns grade based on percentage of total marks.
        """
        self.ensure_one()
        if not self.exam_id or self.status != 'present' or self.marks is None:
            return False
            
        if self.exam_id.total_marks == 0:
            return False
            
        percentage = (self.marks / self.exam_id.total_marks) * 100
        
        # Determine pass/fail based on minimum marks
        if self.marks >= self.exam_id.min_marks:
            return 'pass'
        else:
            return 'fail'
            
    def get_percentage(self):
        """Get percentage score for this attendee.
        
        Returns percentage of marks obtained out of total marks.
        """
        self.ensure_one()
        if not self.exam_id or self.status != 'present' or self.marks is None:
            return 0.0
            
        if self.exam_id.total_marks == 0:
            return 0.0
            
        return (self.marks / self.exam_id.total_marks) * 100
