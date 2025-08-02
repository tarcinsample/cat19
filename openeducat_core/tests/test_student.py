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

from odoo.tests import tagged
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'student')
class TestStudent(TestCoreCommon):
    """Comprehensive tests for op.student model."""

    def test_student_creation_valid_data(self):
        """Test student creation with valid data."""
        student = self._create_test_student(
            first_name='John',
            last_name='Doe',
            birth_date='2000-05-15',
            gender='m'
        )
        
        self.assertEqual(student.first_name, 'John')
        self.assertEqual(student.last_name, 'Doe')
        self.assertEqual(student.name, 'John Doe')
        self.assertEqual(student.gender, 'm')
        self.assertTrue(student.partner_id)
        self.assertTrue(student.active)

    def test_student_onchange_name_with_middle_name(self):
        """Test _onchange_name method with middle name."""
        student = self._create_test_student(
            first_name='John',
            middle_name='William',
            last_name='Doe'
        )
        
        student._onchange_name()
        self.assertEqual(student.name, 'John William Doe')

    def test_student_onchange_name_without_middle_name(self):
        """Test _onchange_name method without middle name."""
        student = self._create_test_student(
            first_name='John',
            last_name='Doe'
        )
        
        student._onchange_name()
        self.assertEqual(student.name, 'John Doe')

    def test_student_onchange_name_only_first_name(self):
        """Test _onchange_name method with only first name."""
        student = self._create_test_student(first_name='John')
        student.last_name = False
        
        student._onchange_name()
        self.assertEqual(student.name, 'John')

    def test_student_onchange_name_only_last_name(self):
        """Test _onchange_name method with only last name."""
        student = self._create_test_student(last_name='Doe')
        student.first_name = False
        
        student._onchange_name()
        self.assertEqual(student.name, 'Doe')

    def test_student_onchange_name_no_names(self):
        """Test _onchange_name method with no names."""
        student = self._create_test_student()
        student.first_name = False
        student.last_name = False
        student.middle_name = False
        
        student._onchange_name()
        self.assertFalse(student.name)

    def test_student_birth_date_validation_future_date(self):
        """Test birth date validation with future date."""
        with self.assertRaises(ValidationError) as cm:
            self._create_test_student(birth_date='2030-01-01')
        
        self.assertIn("Birth date cannot be greater than current date", str(cm.exception))

    def test_student_birth_date_validation_valid_date(self):
        """Test birth date validation with valid date."""
        student = self._create_test_student(birth_date='2000-01-01')
        
        # Should not raise any exception
        student._check_birthdate()
        self.assertEqual(str(student.birth_date), '2000-01-01')

    def test_student_birth_date_validation_none_date(self):
        """Test birth date validation with None date."""
        student = self._create_test_student()
        student.birth_date = False
        
        # Should not raise any exception
        student._check_birthdate()

    def test_student_gr_no_uniqueness_constraint(self):
        """Test that registration number must be unique."""
        # Create first student with gr_no
        student1 = self._create_test_student(gr_no='REG001')
        
        # Try to create second student with same gr_no
        with self.assertRaises(IntegrityError):
            self._create_test_student(gr_no='REG001')

    def test_student_create_user_success(self):
        """Test successful user creation for student."""
        student = self._create_test_student(
            email='student@test.com'
        )
        student.partner_id.email = 'student@test.com'
        
        # Initially no user
        self.assertFalse(student.user_id)
        
        # Create user
        student.create_student_user()
        
        # Verify user created
        self.assertTrue(student.user_id)
        self.assertEqual(student.user_id.login, 'student@test.com')
        self.assertEqual(student.user_id.name, student.name)
        self.assertTrue(student.user_id.is_student)

    def test_student_create_user_already_exists(self):
        """Test user creation when user already exists."""
        student = self._create_test_student()
        
        # Create user first time
        student.create_student_user()
        first_user = student.user_id
        
        # Try to create user again
        student.create_student_user()
        
        # Should still be same user
        self.assertEqual(student.user_id, first_user)

    def test_student_create_user_no_email(self):
        """Test user creation when student has no email."""
        student = self._create_test_student()
        student.partner_id.email = False
        
        # Should still create user but might have different login
        student.create_student_user()
        self.assertTrue(student.user_id)

    def test_student_get_import_templates(self):
        """Test get_import_templates method."""
        templates = self.student_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 1)
        
        template = templates[0]
        self.assertIn('label', template)
        self.assertIn('template', template)
        self.assertEqual(template['template'], '/openeducat_core/static/xls/op_student.xls')

    def test_student_multiple_genders(self):
        """Test student creation with different genders."""
        male_student = self._create_test_student(gender='m')
        female_student = self._create_test_student(gender='f')
        other_student = self._create_test_student(gender='o')
        
        self.assertEqual(male_student.gender, 'm')
        self.assertEqual(female_student.gender, 'f') 
        self.assertEqual(other_student.gender, 'o')

    def test_student_blood_group_options(self):
        """Test student blood group field options."""
        blood_groups = ['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']
        
        for blood_group in blood_groups:
            student = self._create_test_student(blood_group=blood_group)
            self.assertEqual(student.blood_group, blood_group)

    def test_student_partner_relationship(self):
        """Test student partner relationship."""
        student = self._create_test_student(
            first_name='John',
            last_name='Doe'
        )
        
        # Student should have partner
        self.assertTrue(student.partner_id)
        
        # Partner should have student data
        self.assertEqual(student.partner_id.name, student.name)
        
        # Test inherited fields work
        self.assertEqual(student.email, student.partner_id.email)
        self.assertEqual(student.phone, student.partner_id.phone)

    def test_student_course_details_relationship(self):
        """Test student course details one2many relationship."""
        student = self._create_test_student()
        
        # Create course enrollment
        course_detail = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL123'
        )
        
        # Verify relationship
        self.assertIn(course_detail, student.course_detail_ids)
        self.assertEqual(course_detail.student_id, student)

    def test_student_category_relationship(self):
        """Test student category relationship."""
        student = self._create_test_student()
        
        self.assertEqual(student.category_id, self.test_category)
        self.assertEqual(student.category_id.name, 'General Category')

    def test_student_emergency_contact(self):
        """Test student emergency contact field."""
        emergency_partner = self.env['res.partner'].create({
            'name': 'Emergency Contact',
            'phone': '9876543210',
        })
        
        student = self._create_test_student(
            emergency_contact=emergency_partner.id
        )
        
        self.assertEqual(student.emergency_contact, emergency_partner)

    def test_student_certificate_number_readonly(self):
        """Test certificate number field is readonly and not copied."""
        student = self._create_test_student(certificate_number='CERT001')
        
        # Copy student
        copied_student = student.copy()
        
        # Certificate number should not be copied
        self.assertFalse(copied_student.certificate_number)

    def test_student_visa_info(self):
        """Test visa info field for international students."""
        student = self._create_test_student(
            visa_info='F1 Student Visa',
            nationality=self.env.ref('base.us').id
        )
        
        self.assertEqual(student.visa_info, 'F1 Student Visa')
        self.assertEqual(student.nationality.code, 'US')

    def test_student_active_flag(self):
        """Test student active flag functionality."""
        student = self._create_test_student()
        
        # Should be active by default
        self.assertTrue(student.active)
        
        # Deactivate student
        student.active = False
        self.assertFalse(student.active)
        
        # Should not appear in normal searches
        active_students = self.student_model.search([])
        self.assertNotIn(student, active_students)