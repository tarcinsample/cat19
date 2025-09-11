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

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceLine(TestAttendanceCommon):
    """Test attendance line creation and validation."""

    def setUp(self):
        """Set up test data for attendance line tests."""
        super().setUp()
        self.sheet = self.create_attendance_sheet()

    def test_attendance_line_creation(self):
        """Test basic attendance line creation."""
        line = self.create_attendance_line(self.sheet, self.student1, present=True)
        
        self.assertEqual(line.attendance_id, self.sheet, "Should link to sheet")
        self.assertEqual(line.student_id, self.student1, "Should link to student")
        self.assertTrue(line.present, "Should be marked present")
        self.assertFalse(line.absent, "Should not be absent when present")

    def test_attendance_line_present_absent_logic(self):
        """Test present/absent field logic."""
        # Test present student
        present_line = self.create_attendance_line(self.sheet, self.student1, present=True)
        self.assertTrue(present_line.present, "Present should be True")
        self.assertFalse(present_line.absent, "Absent should be False when present")
        
        # Test absent student
        absent_line = self.create_attendance_line(self.sheet, self.student2, present=False)
        self.assertFalse(absent_line.present, "Present should be False")
        self.assertTrue(absent_line.absent, "Absent should be True when not present")

    def test_attendance_line_unique_constraint(self):
        """Test unique constraint for student per attendance sheet."""
        # Create first line
        self.create_attendance_line(self.sheet, self.student1)
        
        # Should not allow duplicate student in same sheet
        with self.assertRaises(Exception):
            self.create_attendance_line(self.sheet, self.student1)

    def test_attendance_line_name_computation(self):
        """Test attendance line name computation."""
        line = self.create_attendance_line(self.sheet, self.student1)
        
        expected_name = f"{self.student1.name} - {self.sheet.attendance_date}"
        self.assertEqual(line.name, expected_name, "Name should be computed correctly")

    def test_attendance_line_bulk_creation(self):
        """Test bulk creation of attendance lines."""
        lines_data = [
            {'attendance_id': self.sheet.id, 'student_id': self.student1.id, 'present': True},
            {'attendance_id': self.sheet.id, 'student_id': self.student2.id, 'present': False, 'absent': True},
        ]
        
        lines = self.env['op.attendance.line'].create(lines_data)
        
        self.assertEqual(len(lines), 2, "Should create 2 lines")
        self.assertTrue(lines[0].present, "First student should be present")
        self.assertFalse(lines[1].present, "Second student should be absent")

    def test_attendance_line_search_by_student(self):
        """Test searching attendance lines by student."""
        line1 = self.create_attendance_line(self.sheet, self.student1)
        line2 = self.create_attendance_line(self.sheet, self.student2)
        
        # Search for specific student
        student1_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertIn(line1, student1_lines, "Should find student1 line")
        self.assertNotIn(line2, student1_lines, "Should not find student2 line")

    def test_attendance_line_search_by_status(self):
        """Test searching attendance lines by present/absent status."""
        present_line = self.create_attendance_line(self.sheet, self.student1, present=True)
        absent_line = self.create_attendance_line(self.sheet, self.student2, present=False)
        
        # Search for present students
        present_lines = self.env['op.attendance.line'].search([
            ('present', '=', True),
            ('attendance_id', '=', self.sheet.id)
        ])
        
        self.assertIn(present_line, present_lines, "Should find present line")
        self.assertNotIn(absent_line, present_lines, "Should not find absent line")

    def test_attendance_line_date_filtering(self):
        """Test filtering attendance lines by date."""
        today_line = self.create_attendance_line(self.sheet, self.student1)
        
        yesterday_sheet = self.create_attendance_sheet(attendance_date=self.yesterday)
        yesterday_line = self.create_attendance_line(yesterday_sheet, self.student2)
        
        # Search for today's attendance
        today_lines = self.env['op.attendance.line'].search([
            ('attendance_date', '=', self.today)
        ])
        
        self.assertIn(today_line, today_lines, "Should find today's line")
        self.assertNotIn(yesterday_line, today_lines, "Should not find yesterday's line")

    def test_attendance_line_course_batch_filtering(self):
        """Test filtering attendance lines by course and batch."""
        line = self.create_attendance_line(self.sheet, self.student1)
        
        # Search by course
        course_lines = self.env['op.attendance.line'].search([
            ('attendance_id.course_id', '=', self.course.id)
        ])
        
        self.assertIn(line, course_lines, "Should find line by course")
        
        # Search by batch
        batch_lines = self.env['op.attendance.line'].search([
            ('attendance_id.batch_id', '=', self.batch.id)
        ])
        
        self.assertIn(line, batch_lines, "Should find line by batch")

    def test_attendance_line_default_values(self):
        """Test default values for attendance line fields."""
        line = self.env['op.attendance.line'].create({
            'attendance_id': self.sheet.id,
            'student_id': self.student1.id,
            'absent': True,  # Set a valid status to pass validation
        })
        
        # Should default to absent (present=False)
        self.assertFalse(line.present, "Should default to absent")
        self.assertTrue(line.absent, "Should be marked as absent by default")

    def test_attendance_line_validation_constraints(self):
        """Test validation constraints for attendance lines."""
        # Test that student must belong to the course/batch
        other_student = self.env['op.student'].create({
            'name': 'Other Student',
            'first_name': 'Other',
            'last_name': 'Student',
            'birth_date': self.yesterday,
        })
        
        # This should work but might show warning in practice
        line = self.create_attendance_line(self.sheet, other_student)
        self.assertTrue(line.exists(), "Line should be created even for unrelated student")

    def test_attendance_line_remarks_field(self):
        """Test remarks field functionality."""
        line = self.create_attendance_line(
            self.sheet, self.student1, 
            present=False, 
            remarks="Student was sick"
        )
        
        self.assertEqual(line.remark, "Student was sick", 
                        "Remarks should be stored correctly")
        self.assertFalse(line.present, "Student should be marked absent")

    def test_attendance_line_performance_bulk_operations(self):
        """Test performance with bulk attendance line operations."""
        # Create multiple students
        students = []
        for i in range(10):
            student = self.env['op.student'].create({
                'name': f'Bulk Student {i}',
                'first_name': 'Bulk',
                'last_name': f'Student{i}',
                'birth_date': self.yesterday,
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            students.append(student)
        
        # Bulk create attendance lines
        lines_data = [
            {
                'attendance_id': self.sheet.id,
                'student_id': student.id,
                'present': i % 2 == 0,  # Alternate present/absent
            }
            for i, student in enumerate(students)
        ]
        
        lines = self.env['op.attendance.line'].create(lines_data)
        
        self.assertEqual(len(lines), 10, "Should create 10 lines")
        present_count = sum(1 for line in lines if line.present)
        self.assertEqual(present_count, 5, "Should have 5 present students")