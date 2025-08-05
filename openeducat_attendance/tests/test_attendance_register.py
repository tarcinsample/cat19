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
class TestAttendanceRegister(TestAttendanceCommon):
    """Test attendance register configuration and validation."""

    def test_attendance_register_creation(self):
        """Test basic attendance register creation."""
        register = self.env['op.attendance.register'].create({
            'name': 'Test Register 2',
            'code': 'TR002',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'subject_id': self.subject.id,
        })
        
        self.assertEqual(register.name, 'Test Register 2', "Name should be set")
        self.assertEqual(register.code, 'TR002', "Code should be set")
        self.assertEqual(register.course_id, self.course, "Course should be set")
        self.assertEqual(register.batch_id, self.batch, "Batch should be set")
        self.assertEqual(register.subject_id, self.subject, "Subject should be set")
        self.assertTrue(register.active, "Should be active by default")

    def test_attendance_register_unique_code_constraint(self):
        """Test unique code constraint for attendance registers."""
        # Create second register with same code
        with self.assertRaises(Exception):
            self.env['op.attendance.register'].create({
                'name': 'Duplicate Register',
                'code': 'TR001',  # Same as existing register
                'course_id': self.course.id,
                'batch_id': self.batch.id,
            })

    def test_attendance_register_unique_combination_constraint(self):
        """Test unique course/batch/subject combination constraint."""
        # Try to create register with same course/batch/subject
        with self.assertRaises(Exception):
            self.env['op.attendance.register'].create({
                'name': 'Duplicate Combination',
                'code': 'TR999',
                'course_id': self.course.id,
                'batch_id': self.batch.id,
                'subject_id': self.subject.id,
            })

    def test_batch_course_consistency_validation(self):
        """Test validation that batch belongs to selected course."""
        # Create another course
        other_course = self.env['op.course'].create({
            'name': 'Other Course',
            'code': 'OC001',
            'department_id': self.department.id,
        })
        
        # Try to create register with mismatched course/batch
        with self.assertRaises(ValidationError):
            self.env['op.attendance.register'].create({
                'name': 'Invalid Register',
                'code': 'IR001',
                'course_id': other_course.id,
                'batch_id': self.batch.id,  # Batch belongs to different course
            })

    def test_attendance_statistics_computation(self):
        """Test attendance statistics computation."""
        # Create attendance sheets
        sheet1 = self.create_attendance_sheet()
        sheet2 = self.create_attendance_sheet(attendance_date=self.yesterday)
        
        # Force computation
        self.register._compute_attendance_statistics()
        
        self.assertEqual(self.register.attendance_sheet_count, 2, 
                        "Should count 2 attendance sheets")
        self.assertEqual(self.register.total_students, 2, 
                        "Should count 2 students in batch")

    def test_course_subject_ids_relation(self):
        """Test course_subject_ids related field."""
        # Add subjects to course
        subject2 = self.env['op.subject'].create({
            'name': 'Test Subject 2',
            'code': 'TS002',
        })
        
        self.course.subject_ids = [(6, 0, [self.subject.id, subject2.id])]
        
        # Check related field
        self.assertIn(self.subject, self.register.course_subject_ids, 
                     "Should include course subjects")
        self.assertIn(subject2, self.register.course_subject_ids, 
                     "Should include all course subjects")

    def test_onchange_course_behavior(self):
        """Test onchange behavior when course is changed."""
        register = self.env['op.attendance.register'].new({
            'name': 'Test Register',
            'code': 'TR003',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'subject_id': self.subject.id,
        })
        
        # Change course
        other_course = self.env['op.course'].create({
            'name': 'Other Course',
            'code': 'OC002',
            'department_id': self.department.id,
        })
        
        register.course_id = other_course
        register.onchange_course()
        
        # Batch and subject should be cleared
        self.assertFalse(register.batch_id, "Batch should be cleared")
        self.assertFalse(register.subject_id, "Subject should be cleared")

    def test_create_attendance_sheet_new(self):
        """Test creating new attendance sheet."""
        action = self.register.create_attendance_sheet()
        
        self.assertEqual(action['res_model'], 'op.attendance.sheet', 
                        "Should return attendance sheet action")
        
        # Check that sheet was created
        sheet = self.env['op.attendance.sheet'].browse(action['res_id'])
        self.assertEqual(sheet.register_id, self.register, 
                        "Sheet should link to register")
        self.assertEqual(sheet.attendance_date, self.today, 
                        "Sheet should have today's date")

    def test_create_attendance_sheet_existing(self):
        """Test behavior when attendance sheet already exists for today."""
        # Create existing sheet
        existing_sheet = self.create_attendance_sheet()
        
        # Try to create another sheet
        action = self.register.create_attendance_sheet()
        
        self.assertEqual(action['res_id'], existing_sheet.id, 
                        "Should return existing sheet")

    def test_attendance_register_ordering(self):
        """Test attendance register ordering."""
        register2 = self.env['op.attendance.register'].create({
            'name': 'Later Register',
            'code': 'LR001',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
        })
        
        registers = self.env['op.attendance.register'].search([
            ('id', 'in', [self.register.id, register2.id])
        ])
        
        # Should be ordered by ID descending (newer first)
        self.assertEqual(registers[0], register2, 
                        "Newer register should come first")

    def test_attendance_register_name_search(self):
        """Test name search functionality."""
        results = self.env['op.attendance.register'].name_search('Test Register')
        
        register_ids = [result[0] for result in results]
        self.assertIn(self.register.id, register_ids, 
                     "Should find register by name")

    def test_attendance_register_code_search(self):
        """Test searching by code."""
        found_registers = self.env['op.attendance.register'].search([
            ('code', '=', 'TR001')
        ])
        
        self.assertIn(self.register, found_registers, 
                     "Should find register by code")

    def test_attendance_register_domain_filters(self):
        """Test domain filters for related fields."""
        # Test subject domain
        register = self.env['op.attendance.register'].new({
            'course_id': self.course.id,
        })
        
        domain_result = register.onchange_course()
        subject_domain = domain_result['domain']['subject_id']
        
        self.assertIn(self.subject.id, subject_domain[0][2], 
                     "Subject should be in domain")

    def test_attendance_register_faculty_assignment(self):
        """Test faculty assignment via attendance sheets (not directly on register)."""
        register = self.env['op.attendance.register'].create({
            'name': 'Faculty Register',
            'code': 'FR001',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'subject_id': self.subject.id,
        })
        
        # Faculty is assigned to attendance sheets, not registers
        sheet = self.env['op.attendance.sheet'].create({
            'register_id': register.id,
            'faculty_id': self.faculty.id,
            'attendance_date': self.today,
        })
        
        self.assertEqual(sheet.faculty_id, self.faculty, 
                        "Faculty should be assigned to attendance sheet")

    def test_attendance_register_active_functionality(self):
        """Test active field functionality."""
        # Test archiving register
        self.register.active = False
        
        # Should not appear in default searches
        active_registers = self.env['op.attendance.register'].search([])
        self.assertNotIn(self.register, active_registers, 
                        "Archived register should not appear in default search")
        
        # Should appear when including archived
        all_registers = self.env['op.attendance.register'].with_context(
            active_test=False).search([('id', '=', self.register.id)])
        self.assertIn(self.register, all_registers, 
                     "Should find archived register with active_test=False")

    def test_attendance_register_tracking_fields(self):
        """Test field tracking functionality."""
        # Modify tracked field
        self.register.name = 'Modified Name'
        
        # Check that change was tracked (message should be created)
        messages = self.register.message_ids
        self.assertTrue(messages, "Should have tracking message")