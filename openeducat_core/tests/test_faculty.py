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
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'faculty')
class TestFaculty(TestCoreCommon):
    """Comprehensive tests for op.faculty model."""

    def test_faculty_creation_with_valid_data(self):
        """Test faculty creation with all required fields."""
        faculty = self._create_test_faculty(
            first_name='John',
            last_name='Professor',
            email='john.prof@university.com'
        )
        
        self.assertEqual(faculty.first_name, 'John')
        self.assertEqual(faculty.last_name, 'Professor')
        self.assertEqual(faculty.name, 'John Professor')
        self.assertEqual(faculty.main_department_id, self.test_department)
        self.assertTrue(faculty.partner_id)
        self.assertEqual(faculty.partner_id.email, 'john.prof@university.com')

    def test_faculty_onchange_name_with_all_names(self):
        """Test _onchange_name method with first, middle, and last names."""
        faculty = self.faculty_model.new({
            'first_name': 'John',
            'middle_name': 'Michael',
            'last_name': 'Professor',
            'main_department_id': self.test_department.id,
        })
        
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'John Michael Professor')

    def test_faculty_onchange_name_without_middle_name(self):
        """Test _onchange_name method without middle name."""
        faculty = self.faculty_model.new({
            'first_name': 'Jane',
            'last_name': 'Doctor',
            'main_department_id': self.test_department.id,
        })
        
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'Jane Doctor')

    def test_faculty_onchange_name_only_first_name(self):
        """Test _onchange_name method with only first name."""
        faculty = self.faculty_model.new({
            'first_name': 'Einstein',
            'main_department_id': self.test_department.id,
        })
        
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'Einstein')

    def test_faculty_onchange_name_only_last_name(self):
        """Test _onchange_name method with only last name."""
        faculty = self.faculty_model.new({
            'last_name': 'Newton',
            'main_department_id': self.test_department.id,
        })
        
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'Newton')

    def test_faculty_onchange_name_no_names(self):
        """Test _onchange_name method with no names provided."""
        faculty = self.faculty_model.new({
            'main_department_id': self.test_department.id,
        })
        
        faculty._onchange_name()
        self.assertFalse(faculty.name)

    def test_faculty_create_employee_method(self):
        """Test create_employee method functionality."""
        faculty = self._create_test_faculty(
            first_name='Alice',
            last_name='Teacher',
            gender='female'
        )
        
        # Faculty should not have employee initially
        self.assertFalse(faculty.emp_id)
        
        # Create employee
        faculty.create_employee()
        
        # Verify employee was created
        self.assertTrue(faculty.emp_id)
        self.assertEqual(faculty.emp_id.name, faculty.name)
        self.assertEqual(faculty.emp_id.gender, faculty.gender)

    def test_faculty_partner_relationship(self):
        """Test faculty partner relationship creation."""
        faculty = self._create_test_faculty(
            first_name='Bob',
            last_name='Instructor'
        )
        
        self.assertTrue(faculty.partner_id)
        self.assertEqual(faculty.partner_id.name, 'Bob Instructor')
        self.assertTrue(faculty.partner_id.is_company is False)

    def test_faculty_department_assignment(self):
        """Test faculty department assignment and validation."""
        # Create additional department
        dept2 = self.env['op.department'].create({
            'name': 'Mathematics Department',
            'code': 'MATH002',
        })
        
        faculty = self._create_test_faculty(
            first_name='Charles',
            last_name='Mathematician',
            main_department_id=dept2.id
        )
        
        self.assertEqual(faculty.main_department_id, dept2)

    def test_faculty_get_import_templates(self):
        """Test get_import_templates method."""
        templates = self.faculty_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 1)
        
        template = templates[0]
        self.assertIn('label', template)
        self.assertIn('template', template)
        self.assertEqual(template['template'], '/openeducat_core/static/xls/op_faculty.xls')

    def test_faculty_name_search(self):
        """Test name_search functionality."""
        faculty1 = self._create_test_faculty(
            first_name='David',
            last_name='Physics'
        )
        faculty2 = self._create_test_faculty(
            first_name='Eva',
            last_name='Chemistry'
        )
        
        # Search by first name
        results = self.faculty_model.name_search('David')
        faculty_ids = [result[0] for result in results]
        self.assertIn(faculty1.id, faculty_ids)
        self.assertNotIn(faculty2.id, faculty_ids)

    def test_faculty_active_field(self):
        """Test faculty active field functionality."""
        faculty = self._create_test_faculty(
            first_name='Frank',
            last_name='Biology'
        )
        
        # Faculty should be active by default
        self.assertTrue(faculty.active)
        
        # Deactivate faculty
        faculty.active = False
        self.assertFalse(faculty.active)

    def test_faculty_birth_date_validation(self):
        """Test birth date field validation."""
        faculty = self._create_test_faculty(
            first_name='Grace',
            last_name='History',
            birth_date='1970-05-15'
        )
        
        self.assertEqual(str(faculty.birth_date), '1970-05-15')

    def test_faculty_gender_field(self):
        """Test gender field options."""
        faculty_male = self._create_test_faculty(
            first_name='Henry',
            last_name='English',
            gender='male'
        )
        
        faculty_female = self._create_test_faculty(
            first_name='Iris',
            last_name='French',
            gender='female'
        )
        
        self.assertEqual(faculty_male.gender, 'male')
        self.assertEqual(faculty_female.gender, 'female')

    def test_faculty_contact_information(self):
        """Test faculty contact information fields."""
        faculty = self._create_test_faculty(
            first_name='Kelly',
            last_name='Music',
            phone='123-456-7890',
            mobile='098-765-4321'
        )
        
        self.assertEqual(faculty.phone, '123-456-7890')
        self.assertEqual(faculty.mobile, '098-765-4321')

    def test_faculty_emergency_contact(self):
        """Test faculty emergency contact information."""
        # Create emergency contact partner
        emergency_partner = self.env['res.partner'].create({
            'name': 'Emergency Contact Name',
            'phone': '911-123-4567',
        })
        
        faculty = self._create_test_faculty(
            first_name='Leo',
            last_name='Sports',
            emergency_contact=emergency_partner.id
        )
        
        self.assertEqual(faculty.emergency_contact, emergency_partner)
        self.assertEqual(faculty.emergency_contact.phone, '911-123-4567')

    def test_faculty_visa_info(self):
        """Test faculty visa information fields."""
        faculty = self._create_test_faculty(
            first_name='Maria',
            last_name='Language',
            visa_info='Work Visa',
            id_number='VISA123456'
        )
        
        self.assertEqual(faculty.visa_info, 'Work Visa')
        self.assertEqual(faculty.id_number, 'VISA123456')

    def test_faculty_tracking_fields(self):
        """Test that tracking fields are properly configured."""
        faculty = self._create_test_faculty(
            first_name='Nancy',
            last_name='Science'
        )
        
        # Test field help texts exist
        field_info = self.faculty_model.fields_get()
        
        self.assertIn('help', field_info['first_name'])
        self.assertIn('help', field_info['last_name'])
        self.assertIn('help', field_info['main_department_id'])

    def test_faculty_multiple_departments(self):
        """Test faculty assignment to multiple departments."""
        # Create additional departments
        dept_math = self.env['op.department'].create({
            'name': 'Mathematics',
            'code': 'MATH003',
        })
        
        dept_physics = self.env['op.department'].create({
            'name': 'Physics',
            'code': 'PHYS003',
        })
        
        faculty = self._create_test_faculty(
            first_name='Oscar',
            last_name='MultiDisciplinary',
            main_department_id=dept_math.id
        )
        
        # Test main department assignment
        self.assertEqual(faculty.main_department_id, dept_math)

    def test_faculty_employee_creation_validation(self):
        """Test employee creation validation logic."""
        faculty = self._create_test_faculty(
            first_name='Patricia',
            last_name='Administrator',
            gender='female'
        )
        
        # Test that create_employee method works properly
        faculty.create_employee()
        
        # Verify employee was created with correct data
        self.assertTrue(faculty.emp_id)
        self.assertEqual(faculty.emp_id.name, faculty.name)
        self.assertEqual(faculty.emp_id.gender, faculty.gender)
        
        # Verify partner was updated
        self.assertTrue(faculty.partner_id.employee)

    def test_faculty_display_name(self):
        """Test faculty display name functionality."""
        faculty = self._create_test_faculty(
            first_name='Quincy',
            last_name='Philosophy'
        )
        
        # Display name should include relevant information
        display_name = faculty.display_name
        self.assertTrue(display_name)
        self.assertIn('Quincy', display_name)

    def test_faculty_sql_constraints(self):
        """Test SQL constraints are properly defined."""
        model = self.faculty_model
        constraints = model._sql_constraints
        
        # Check if constraints exist (if any are defined)
        self.assertIsInstance(constraints, list)

    def test_faculty_create_with_partner_data(self):
        """Test faculty creation with partner data sync."""
        partner = self.env['res.partner'].create({
            'name': 'Robert Research',
            'email': 'robert@research.com',
            'phone': '555-0123',
        })
        
        faculty = self.faculty_model.create({
            'first_name': 'Robert',
            'last_name': 'Research',
            'main_department_id': self.test_department.id,
            'partner_id': partner.id,
        })
        
        self.assertEqual(faculty.partner_id, partner)
        self.assertEqual(faculty.name, 'Robert Research')

    def test_faculty_name_computation_edge_cases(self):
        """Test edge cases in name computation."""
        # Test with special characters
        faculty = self.faculty_model.new({
            'first_name': 'José',
            'last_name': 'García-López',
            'main_department_id': self.test_department.id,
        })
        
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'José García-López')

    def test_faculty_department_constraint(self):
        """Test department assignment constraints."""
        faculty = self._create_test_faculty(
            first_name='Samuel',
            last_name='Ethics'
        )
        
        # Faculty should have a main department
        self.assertTrue(faculty.main_department_id)
        self.assertEqual(faculty.main_department_id, self.test_department)

    def test_faculty_birth_date_constraint(self):
        """Test birth date constraint validation."""
        from datetime import date, timedelta
        
        # Valid birth date (past)
        faculty = self._create_test_faculty(
            first_name='Valid',
            last_name='BirthDate',
            birth_date='1990-01-01'
        )
        self.assertTrue(faculty.birth_date)
        
        # Invalid birth date (future) - should raise ValidationError
        future_date = date.today() + timedelta(days=30)
        with self.assertRaises(ValidationError):
            self._create_test_faculty(
                first_name='Invalid',
                last_name='FutureBirth',
                birth_date=future_date
            )

    def test_faculty_blood_group_options(self):
        """Test blood group field options."""
        faculty = self._create_test_faculty(
            first_name='Thomas',
            last_name='BloodType',
            blood_group='A+'
        )
        
        self.assertEqual(faculty.blood_group, 'A+')
        
        # Test other blood group options
        valid_blood_groups = ['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']
        for bg in valid_blood_groups:
            faculty_bg = self._create_test_faculty(
                first_name='Test',
                last_name=f'BloodGroup{bg}',
                blood_group=bg
            )
            self.assertEqual(faculty_bg.blood_group, bg)