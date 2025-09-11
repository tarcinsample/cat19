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

from datetime import date, datetime, timedelta
import uuid
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceCommon(TransactionCase):
    """Common test setup for attendance module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for attendance tests."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create academic year
        cls.academic_year = cls.env['op.academic.year'].create({
            'name': 'Test Year 2024-25',
            'start_date': date(2024, 6, 1),
            'end_date': date(2025, 5, 31),
        })
        
        # Create academic term
        cls.academic_term = cls.env['op.academic.term'].create({
            'name': 'Test Term 1',
            'term_start_date': date(2024, 6, 1),
            'term_end_date': date(2024, 12, 31),
            'academic_year_id': cls.academic_year.id,
        })
        
        # Create department
        cls.department = cls.env['op.department'].create({
            'name': 'Test Department',
            'code': 'TD001',
        })
        
        # Create course
        cls.course = cls.env['op.course'].create({
            'name': 'Test Course',
            'code': 'TC001',
            'department_id': cls.department.id,
        })
        
        # Create subject
        cls.subject = cls.env['op.subject'].create({
            'name': 'Test Subject',
            'code': 'TS001',
        })
        
        # Create batch
        cls.batch = cls.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'TB001_' + str(uuid.uuid4())[:8].replace('-', ''),
            'course_id': cls.course.id,
            'start_date': date(2024, 6, 1),
            'end_date': date(2024, 12, 31),
        })
        
        # Create faculty with required fields
        faculty_partner = cls.env['res.partner'].create({
            'name': 'Test Faculty',
            'is_company': False,
        })
        cls.faculty = cls.env['op.faculty'].create({
            'partner_id': faculty_partner.id,
            'first_name': 'Test',
            'last_name': 'Faculty',
            'birth_date': date(1980, 1, 1),
            'gender': 'male',
            'faculty_subject_ids': [(6, 0, [cls.subject.id])],
        })
        
        # Create students with required partners
        partner1 = cls.env['res.partner'].create({
            'name': 'Test Student 1',
            'is_company': False,
        })
        cls.student1 = cls.env['op.student'].create({
            'partner_id': partner1.id,
            'first_name': 'Test',
            'last_name': 'Student1',
            'birth_date': date(2000, 1, 1),
            'gender': 'm',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        partner2 = cls.env['res.partner'].create({
            'name': 'Test Student 2',
            'is_company': False,
        })
        cls.student2 = cls.env['op.student'].create({
            'partner_id': partner2.id,
            'first_name': 'Test',
            'last_name': 'Student2',
            'birth_date': date(2000, 2, 2),
            'gender': 'f',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        # Create attendance register
        cls.register = cls.env['op.attendance.register'].create({
            'name': 'Test Register',
            'code': 'TR001',
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'subject_id': cls.subject.id,
        })
        
        # Create attendance session with all required fields
        cls.session = cls.env['op.session'].create({
            'course_id': cls.course.id,
            'faculty_id': cls.faculty.id,
            'batch_id': cls.batch.id,
            'subject_id': cls.subject.id,
            'start_datetime': datetime.now(),
            'end_datetime': datetime.now() + timedelta(hours=1),
        })
        
        # Model references for legacy tests
        cls.op_attendance_register = cls.env['op.attendance.register']
        cls.op_attendance_sheet = cls.env['op.attendance.sheet']
        cls.op_attendance_line = cls.env['op.attendance.line']
        cls.op_attendance_wizard = cls.env['student.attendance']
        
        # Helper methods
        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)

    def create_attendance_sheet(self, **kwargs):
        """Helper method to create attendance sheet."""
        vals = {
            'register_id': self.register.id,
            'attendance_date': self.today,
        }
        vals.update(kwargs)
        return self.env['op.attendance.sheet'].create(vals)

    def create_attendance_line(self, sheet, student, present=True, **kwargs):
        """Helper method to create attendance line."""
        vals = {
            'attendance_id': sheet.id,
            'student_id': student.id,
            'present': present,
        }
        # If not present, set absent status by default (unless other status is specified)
        if not present and not any(k in kwargs for k in ['absent', 'excused', 'late']):
            vals['absent'] = True
            
        # Handle remarks -> remark field name mapping
        if 'remarks' in kwargs:
            kwargs['remark'] = kwargs.pop('remarks')
        vals.update(kwargs)
        return self.env['op.attendance.line'].create(vals)

    def assert_sheet_state(self, sheet, expected_state):
        """Helper method to assert sheet state."""
        self.assertEqual(sheet.state, expected_state,
                        f"Expected sheet state: {expected_state}, "
                        f"actual: {sheet.state}")
