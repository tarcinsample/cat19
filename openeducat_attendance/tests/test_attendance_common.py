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

from datetime import date, timedelta
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
            'code': 'TY24',
            'date_start': date(2024, 6, 1),
            'date_stop': date(2025, 5, 31),
        })
        
        # Create academic term
        cls.academic_term = cls.env['op.academic.term'].create({
            'name': 'Test Term 1',
            'code': 'TT1',
            'term_start_date': date(2024, 6, 1),
            'term_end_date': date(2024, 12, 31),
            'parent_id': cls.academic_year.id,
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
            'code': 'TB001',
            'course_id': cls.course.id,
            'start_date': date(2024, 6, 1),
            'end_date': date(2024, 12, 31),
        })
        
        # Create faculty
        cls.faculty = cls.env['op.faculty'].create({
            'name': 'Test Faculty',
            'faculty_subject_ids': [(6, 0, [cls.subject.id])],
        })
        
        # Create students
        cls.student1 = cls.env['op.student'].create({
            'name': 'Test Student 1',
            'first_name': 'Test',
            'last_name': 'Student1',
            'birth_date': date(2000, 1, 1),
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        cls.student2 = cls.env['op.student'].create({
            'name': 'Test Student 2',
            'first_name': 'Test',
            'last_name': 'Student2',
            'birth_date': date(2000, 2, 2),
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
            'faculty_id': cls.faculty.id,
        })
        
        # Create attendance session
        cls.session = cls.env['op.session'].create({
            'name': 'Test Session',
        })
        
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
        vals.update(kwargs)
        return self.env['op.attendance.line'].create(vals)

    def assert_sheet_state(self, sheet, expected_state):
        """Helper method to assert sheet state."""
        self.assertEqual(sheet.state, expected_state,
                        f"Expected sheet state: {expected_state}, "
                        f"actual: {sheet.state}")
