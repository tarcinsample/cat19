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

from odoo import _, fields, http
from odoo.http import request
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class OpAttendanceController(http.Controller):

    @http.route(['/openeducat-attendance/take-attendance'], type='json',
                auth='user', methods=['POST'], csrf=False)
    def create_attendance_lines(self, **post):
        """Create attendance lines for students in batch.
        
        Optimized batch creation with proper error handling and validation.
        
        Args:
            **post: Request data containing attendance_sheet_id
            
        Returns:
            dict: Result with success status and created count
        """
        try:
            sheet_id = post.get('attendance_sheet_id')
            if not sheet_id:
                return {
                    'success': False,
                    'error': _('Attendance sheet ID is required')
                }
            
            # Get attendance sheet with validation
            sheet = request.env['op.attendance.sheet'].browse(sheet_id)
            if not sheet.exists():
                return {
                    'success': False,
                    'error': _('Invalid attendance sheet ID')
                }
            
            if not sheet.register_id:
                return {
                    'success': False,
                    'error': _('Attendance sheet must have a register')
                }
            
            # Find all active students in the batch
            students = request.env['op.student'].search([
                ('course_detail_ids.course_id', '=', sheet.register_id.course_id.id),
                ('course_detail_ids.batch_id', '=', sheet.register_id.batch_id.id),
                ('active', '=', True)
            ])
            
            if not students:
                return {
                    'success': False,
                    'error': _('No students found for this course and batch')
                }
            
            # Get existing attendance lines to avoid duplicates
            existing_lines = request.env['op.attendance.line'].search([
                ('attendance_id', '=', sheet.id)
            ])
            existing_student_ids = set(existing_lines.mapped('student_id.id'))
            
            # Prepare attendance lines for new students
            attendance_vals = []
            for student in students:
                if student.id not in existing_student_ids:
                    attendance_vals.append({
                        'attendance_id': sheet.id,
                        'student_id': student.id,
                        'attendance_date': sheet.attendance_date or fields.Date.today(),
                        'present': False  # Default to absent for manual marking
                    })
            
            # Batch create attendance lines
            created_lines = 0
            if attendance_vals:
                request.env['op.attendance.line'].create(attendance_vals)
                created_lines = len(attendance_vals)
                _logger.info(
                    "Created %d attendance lines for sheet %d", 
                    created_lines, sheet.id)
            
            return {
                'success': True,
                'created_count': created_lines,
                'total_students': len(students),
                'message': _('%d attendance lines created successfully') % created_lines
            }
            
        except Exception as e:
            _logger.error("Error creating attendance lines: %s", str(e))
            return {
                'success': False,
                'error': _('Error creating attendance lines: %s') % str(e)
            }
