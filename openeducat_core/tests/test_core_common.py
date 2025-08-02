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


from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestCoreCommon(TransactionCase):
    """Common setup for OpenEduCat core module tests."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Disable tracking for performance
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create test company
        cls.test_company = cls.env.ref('base.main_company')
        
        # Create test department
        cls.test_department = cls.env['op.department'].create({
            'name': 'Test Department',
            'code': 'TEST001',
        })
        
        # Create test program level
        cls.test_program_level = cls.env['op.program.level'].create({
            'name': 'Bachelor Degree',
        })
        
        # Create test program
        cls.test_program = cls.env['op.program'].create({
            'name': 'Computer Science',
            'code': 'CS001',
            'department_id': cls.test_department.id,
            'program_level_id': cls.test_program_level.id,
        })
        
        # Create test course
        cls.test_course = cls.env['op.course'].create({
            'name': 'Data Structures',
            'code': 'CS101',
            'department_id': cls.test_department.id,
            'program_id': cls.test_program.id,
        })
        
        # Create test batch
        cls.test_batch = cls.env['op.batch'].create({
            'name': 'Batch 2024',
            'code': 'B2024',
            'course_id': cls.test_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Create test partner for student
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Test Student Partner',
            'email': 'student@test.com',
            'phone': '1234567890',
        })
        
        # Create test category
        cls.test_category = cls.env['op.category'].create({
            'name': 'General Category',
            'code': 'GEN',
        })
        
        # Create test subject
        cls.test_subject = cls.env['op.subject'].create({
            'name': 'Mathematics',
            'code': 'MATH101',
            'type': 'theory',
            'subject_type': 'compulsory',
            'department_id': cls.test_department.id,
        })
        
        # Add subject to course
        cls.test_course.subject_ids = [(6, 0, [cls.test_subject.id])]

    def setUp(self):
        super().setUp()
        
        # Initialize model references
        self.student_model = self.env['op.student']
        self.faculty_model = self.env['op.faculty'] 
        self.batch_model = self.env['op.batch']
        self.course_model = self.env['op.course']
        self.subject_registration_model = self.env['op.subject.registration']
        
    def _create_test_student(self, **kwargs):
        """Helper method to create a test student with default values."""
        partner = self.env['res.partner'].create({
            'name': kwargs.get('name', 'Test Student'),
            'email': kwargs.get('email', 'test@student.com'),
        })
        
        defaults = {
            'first_name': 'Test',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'partner_id': partner.id,
            'category_id': self.test_category.id,
        }
        defaults.update(kwargs)
        # Remove name from kwargs as it's computed
        defaults.pop('name', None)
        defaults.pop('email', None)
        
        return self.student_model.create(defaults)
        
    def _create_test_faculty(self, **kwargs):
        """Helper method to create a test faculty with default values."""
        partner = self.env['res.partner'].create({
            'name': kwargs.get('name', 'Test Faculty'),
            'email': kwargs.get('email', 'test@faculty.com'),
        })
        
        defaults = {
            'first_name': 'Test',
            'last_name': 'Faculty', 
            'birth_date': '1980-01-01',
            'gender': 'male',
            'partner_id': partner.id,
            'main_department_id': self.test_department.id,
        }
        defaults.update(kwargs)
        # Remove name from kwargs as it's computed
        defaults.pop('name', None)
        defaults.pop('email', None)
        
        return self.faculty_model.create(defaults)
        
    def _create_test_student_course(self, **kwargs):
        """Helper method to create a test student course enrollment."""
        # Generate unique roll number if not provided
        import time
        unique_suffix = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        
        defaults = {
            'course_id': self.test_course.id,
            'batch_id': self.test_batch.id,
            'roll_number': kwargs.get('roll_number', f'ROLL{unique_suffix}'),
        }
        defaults.update(kwargs)
        
        return self.env['op.student.course'].create(defaults)
