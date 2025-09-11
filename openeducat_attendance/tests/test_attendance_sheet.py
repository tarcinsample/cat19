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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceSheet(TestAttendanceCommon):
    """Test attendance sheet generation and management."""

    def test_attendance_sheet_creation(self):
        """Test basic attendance sheet creation."""
        sheet = self.create_attendance_sheet()
        
        self.assertTrue(sheet.name, "Attendance sheet should have generated name")
        self.assertIn('TR001', sheet.name, "Sheet name should contain register code")
        self.assertEqual(sheet.register_id, self.register, "Register should be set")
        self.assertEqual(sheet.attendance_date, self.today, "Date should be today")
        self.assertEqual(sheet.state, 'draft', "Initial state should be draft")

    def test_attendance_sheet_sequence_generation(self):
        """Test unique sequence generation for attendance sheets."""
        sheet1 = self.create_attendance_sheet()
        sheet2 = self.create_attendance_sheet()
        
        self.assertNotEqual(sheet1.name, sheet2.name, 
                           "Each sheet should have unique name")
        self.assertTrue(all('TR001' in name for name in [sheet1.name, sheet2.name]),
                       "Both sheets should contain register code")

    def test_attendance_sheet_workflow_transitions(self):
        """Test attendance sheet state transitions."""
        sheet = self.create_attendance_sheet()
        
        # Test draft to start transition
        sheet.attendance_start()
        self.assert_sheet_state(sheet, 'start')
        
        # Create attendance lines for completion
        self.create_attendance_line(sheet, self.student1)
        
        # Test start to done transition
        sheet.attendance_done()
        self.assert_sheet_state(sheet, 'done')
        
        # Test cancellation
        sheet.attendance_cancel()
        self.assert_sheet_state(sheet, 'cancel')

    def test_attendance_sheet_date_validation(self):
        """Test attendance date validation constraints."""
        # Test future date validation
        with self.assertRaises(ValidationError):
            self.create_attendance_sheet(attendance_date=self.tomorrow)

    def test_attendance_sheet_unique_constraint(self):
        """Test unique constraint for register/session/date combination."""
        sheet1 = self.create_attendance_sheet(session_id=self.session.id)
        
        # Should raise constraint error for duplicate
        with self.assertRaises(Exception):
            self.create_attendance_sheet(session_id=self.session.id)

    def test_generate_attendance_lines(self):
        """Test automatic generation of attendance lines for students."""
        sheet = self.create_attendance_sheet()
        
        # Generate attendance lines
        count = sheet.generate_attendance_lines()
        
        self.assertEqual(count, 2, "Should create lines for 2 students")
        self.assertEqual(len(sheet.attendance_line), 2, 
                        "Sheet should have 2 attendance lines")
        
        # Check student assignments
        student_ids = sheet.attendance_line.mapped('student_id.id')
        self.assertIn(self.student1.id, student_ids, "Student1 should be in attendance")
        self.assertIn(self.student2.id, student_ids, "Student2 should be in attendance")

    def test_generate_attendance_lines_no_duplicates(self):
        """Test that generating lines twice doesn't create duplicates."""
        sheet = self.create_attendance_sheet()
        
        # First generation
        count1 = sheet.generate_attendance_lines()
        self.assertEqual(count1, 2, "First generation should create 2 lines")
        
        # Second generation should not create duplicates
        count2 = sheet.generate_attendance_lines()
        self.assertEqual(count2, 0, "Second generation should create 0 new lines")
        self.assertEqual(len(sheet.attendance_line), 2, 
                        "Should still have only 2 lines")

    def test_attendance_draft_with_lines_validation(self):
        """Test that sheet with lines cannot be set to draft."""
        sheet = self.create_attendance_sheet()
        sheet.attendance_start()
        
        # Add attendance line
        self.create_attendance_line(sheet, self.student1)
        
        # Should not allow draft state with existing lines
        with self.assertRaises(ValidationError):
            sheet.attendance_draft()

    def test_attendance_start_validation(self):
        """Test attendance start validation requirements."""
        # Test without register
        sheet = self.env['op.attendance.sheet'].create({
            'attendance_date': self.today,
        })
        
        with self.assertRaises(ValidationError):
            sheet.attendance_start()

    def test_attendance_done_validation(self):
        """Test attendance completion validation."""
        sheet = self.create_attendance_sheet()
        sheet.attendance_start()
        
        # Should not allow completion without attendance lines
        with self.assertRaises(ValidationError):
            sheet.attendance_done()

    def test_related_fields_computation(self):
        """Test related field computation from register."""
        sheet = self.create_attendance_sheet()
        
        self.assertEqual(sheet.course_id, self.course, 
                        "Course should be related from register")
        self.assertEqual(sheet.batch_id, self.batch, 
                        "Batch should be related from register")

    def test_attendance_sheet_ordering(self):
        """Test attendance sheet ordering by date."""
        yesterday_sheet = self.create_attendance_sheet(
            attendance_date=self.yesterday)
        today_sheet = self.create_attendance_sheet()
        
        sheets = self.env['op.attendance.sheet'].search([
            ('id', 'in', [yesterday_sheet.id, today_sheet.id])
        ])
        
        # Should be ordered by date descending
        self.assertEqual(sheets[0], today_sheet, 
                        "Today's sheet should come first")
        self.assertEqual(sheets[1], yesterday_sheet, 
                        "Yesterday's sheet should come second")