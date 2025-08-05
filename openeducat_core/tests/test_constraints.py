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
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'constraints')
class TestConstraints(TestCoreCommon):
    """Test all constraint methods and business logic validation."""

    def test_student_birth_date_constraint(self):
        """Test student birth date constraint validation."""
        # Valid birth date (past date)
        student = self._create_test_student(birth_date='2000-01-01')
        student._check_birthdate()  # Should not raise exception
        
        # Invalid birth date (future date)
        with self.assertRaises(ValidationError) as context:
            self._create_test_student(birth_date='2030-01-01')
        
        self.assertIn("Birth date cannot be greater than current date", 
                     str(context.exception))

    def test_student_birth_date_edge_cases(self):
        """Test student birth date constraint edge cases."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Today's date should be valid
        student_today = self._create_test_student(birth_date=today)
        student_today._check_birthdate()  # Should not raise exception
        
        # Yesterday should be valid
        student_yesterday = self._create_test_student(birth_date=yesterday)
        student_yesterday._check_birthdate()  # Should not raise exception
        
        # Tomorrow should be invalid
        student_future = self._create_test_student()
        student_future.birth_date = tomorrow
        with self.assertRaises(ValidationError):
            student_future._check_birthdate()

    def test_student_birth_date_none_handling(self):
        """Test student birth date constraint with None values."""
        student = self._create_test_student()
        student.birth_date = None
        
        # None birth date should not raise exception
        try:
            student._check_birthdate()
        except ValidationError:
            self.fail("Birth date constraint should handle None values gracefully")

    def test_faculty_birth_date_constraint(self):
        """Test faculty birth date constraint validation."""
        # Valid birth date
        faculty = self._create_test_faculty(birth_date='1980-01-01')
        if hasattr(faculty, '_check_birthdate'):
            faculty._check_birthdate()  # Should not raise exception
        
        # Invalid birth date (if constraint exists)
        faculty_future = self._create_test_faculty()
        faculty_future.birth_date = '2030-01-01'
        if hasattr(faculty_future, '_check_birthdate'):
            with self.assertRaises(ValidationError):
                faculty_future._check_birthdate()

    def test_batch_date_constraint(self):
        """Test batch date constraint validation."""
        # Valid dates (start before end)
        batch = self.env['op.batch'].create({
            'name': 'Valid Batch',
            
            'course_id': self.test_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        batch.check_dates()  # Should not raise exception
        
        # Invalid dates (end before start)
        with self.assertRaises(ValidationError) as context:
            self.env['op.batch'].create({
                'name': 'Invalid Batch',
                
                'course_id': self.test_course.id,
                'start_date': '2024-12-31',
                'end_date': '2024-01-01',
            })
        
        self.assertIn("End Date cannot be set before Start Date", 
                     str(context.exception))

    def test_batch_date_constraint_same_dates(self):
        """Test batch date constraint with same start and end dates."""
        # Same start and end date should be valid
        batch = self.env['op.batch'].create({
            'name': 'Same Date Batch',
            
            'course_id': self.test_course.id,
            'start_date': '2024-06-15',
            'end_date': '2024-06-15',
        })
        batch.check_dates()  # Should not raise exception

    def test_batch_date_constraint_none_handling(self):
        """Test batch date constraint with None values."""
        batch = self.env['op.batch'].create({
            'name': 'None Date Batch',
            
            'course_id': self.test_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Test with None end date
        batch.end_date = None
        try:
            batch.check_dates()
        except ValidationError:
            self.fail("Batch date constraint should handle None values gracefully")
        
        # Test with None start date
        batch.start_date = None
        batch.end_date = '2024-12-31'
        try:
            batch.check_dates()
        except ValidationError:
            self.fail("Batch date constraint should handle None values gracefully")

    def test_course_recursive_constraint(self):
        """Test course recursive category constraint."""
        # Create parent course
        parent_course = self.env['op.course'].create({
            'name': 'Parent Course',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        # Create child course
        child_course = self.env['op.course'].create({
            'name': 'Child Course',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'academic_year_id': parent_course.id,
        })
        
        # Test normal hierarchy (should be valid)
        child_course._check_category_recursion()
        
        # Test circular reference (should be invalid)
        with self.assertRaises(ValidationError) as context:
            parent_course.parent_id = child_course.id
        
        self.assertIn("recursive categories", str(context.exception))

    def test_course_self_parent_constraint(self):
        """Test course cannot be its own parent."""
        course = self.env['op.course'].create({
            'name': 'Self Parent Course',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        # Try to set course as its own parent
        with self.assertRaises(ValidationError):
            course.parent_id = course.id

    def test_course_complex_recursion_constraint(self):
        """Test course complex recursion scenarios."""
        # Create multi-level hierarchy
        level1 = self.env['op.course'].create({
            'name': 'Level 1',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        level2 = self.env['op.course'].create({
            'name': 'Level 2',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'academic_year_id': level1.id,
        })
        
        level3 = self.env['op.course'].create({
            'name': 'Level 3',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'academic_year_id': level2.id,
        })
        
        # Try to create circular reference (level1 -> level3)
        with self.assertRaises(ValidationError):
            level1.parent_id = level3.id

    def test_academic_year_date_constraint(self):
        """Test academic year date constraint if exists."""
        # Valid academic year
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Test if date constraint exists
        if hasattr(academic_year, '_check_dates'):
            academic_year._check_dates()

    def test_academic_term_date_constraint(self):
        """Test academic term date constraint if exists."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Valid academic term
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'term_start_date': '2024-01-01',
            'term_end_date': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # Test if date constraint exists
        if hasattr(academic_term, '_check_dates'):
            academic_term._check_dates()

    def test_sql_constraints_uniqueness(self):
        """Test SQL uniqueness constraints."""
        # Test student gr_no uniqueness
        student1 = self._create_test_student(gr_no='UNIQUE001')
        
        with self.assertRaises(IntegrityError):
            self._create_test_student(gr_no='UNIQUE001')
        
        # Test course code uniqueness
        course1 = self.env['op.course'].create({
            'name': 'First Course',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        with self.assertRaises(IntegrityError):
            self.env['op.course'].create({
                'name': 'Second Course',
                  # Duplicate code
                'department_id': self.test_department.id,
                'program_id': self.test_program.id,
            })
        
        # Test batch code uniqueness
        batch1 = self.env['op.batch'].create({
            'name': 'First Batch',
            
            'course_id': self.test_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        with self.assertRaises(IntegrityError):
            self.env['op.batch'].create({
                'name': 'Second Batch',
                  # Duplicate code
                'course_id': self.test_course.id,
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
            })

    def test_required_field_constraints(self):
        """Test required field constraints."""
        # Test student required fields
        with self.assertRaises(Exception):
            self.env['op.student'].create({
                # Missing required fields
                'birth_date': '2000-01-01',
            })
        
        # Test course required fields
        with self.assertRaises(Exception):
            self.env['op.course'].create({
                # Missing name and code
                'department_id': self.test_department.id,
            })
        
        # Test batch required fields
        with self.assertRaises(Exception):
            self.env['op.batch'].create({
                # Missing required fields
                'start_date': '2024-01-01',
            })

    def test_domain_constraints(self):
        """Test domain-based constraints."""
        # Test valid gender values for student
        valid_genders = ['m', 'f', 'o']
        for gender in valid_genders:
            student = self._create_test_student(gender=gender)
            self.assertEqual(student.gender, gender)
        
        # Test valid subject types
        valid_types = ['theory', 'practical', 'both']
        for subject_type in valid_types:
            subject = self.env['op.subject'].create({
                'name': f'Test Subject {subject_type}',
                'code': f'TS_{subject_type.upper()}',
                'type': subject_type,
                'subject_type': 'compulsory',
                'department_id': self.test_department.id,
            })
            self.assertEqual(subject.type, subject_type)

    def test_constraint_error_messages(self):
        """Test constraint error messages are meaningful."""
        # Test birth date constraint message
        try:
            self._create_test_student(birth_date='2030-01-01')
        except ValidationError as e:
            self.assertIn("Birth date cannot be greater than current date", 
                         str(e))
        
        # Test batch date constraint message
        try:
            self.env['op.batch'].create({
                'name': 'Invalid Batch',
                
                'course_id': self.test_course.id,
                'start_date': '2024-12-31',
                'end_date': '2024-01-01',
            })
        except ValidationError as e:
            self.assertIn("End Date cannot be set before Start Date", str(e))
        
        # Test course recursion constraint message
        try:
            course = self.env['op.course'].create({
                'name': 'Test Course',
                
                'department_id': self.test_department.id,
                'program_id': self.test_program.id,
            })
            course.parent_id = course.id
        except ValidationError as e:
            self.assertIn("recursive categories", str(e))

    def test_multiple_constraint_validation(self):
        """Test multiple constraints working together."""
        # Create student with multiple potential constraint violations
        student = self._create_test_student(
            birth_date='2000-01-01',  # Valid
            gr_no='MULTI001'  # Valid
        )
        
        # Test changing to invalid birth date
        with self.assertRaises(ValidationError):
            student.birth_date = '2030-01-01'
        
        # Test duplicate gr_no
        with self.assertRaises(IntegrityError):
            self._create_test_student(gr_no='MULTI001')

    def test_constraint_performance(self):
        """Test constraint validation performance with bulk operations."""
        # Create multiple students to test constraint performance
        students = []
        for i in range(20):
            student = self._create_test_student(
                first_name=f'Student{i}',
                last_name=f'Test{i}',
                birth_date='2000-01-01',
                gr_no=f'PERF{i:03d}'
            )
            students.append(student)
        
        # All students should be created successfully
        self.assertEqual(len(students), 20)
        
        # Test constraint validation on batch update
        for student in students:
            student.birth_date = '1999-01-01'  # Valid date
        
        # All updates should succeed
        for student in students:
            self.assertEqual(str(student.birth_date), '1999-01-01')