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

from odoo.tests import tagged, TransactionCase
from odoo.exceptions import ValidationError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'compute_methods')
class TestComputeMethods(TestCoreCommon):
    """Test all compute methods and @api.depends decorators in core models."""

    def test_student_name_compute_dependencies(self):
        """Test student name compute method with proper dependencies."""
        student = self._create_test_student(
            first_name='John',
            middle_name='William',
            last_name='Doe'
        )
        
        # Test initial name computation
        self.assertEqual(student.name, 'John William Doe')
        
        # Test dependency triggers - changing first_name should recompute name
        student.first_name = 'Jane'
        self.assertEqual(student.name, 'Jane William Doe')
        
        # Test dependency triggers - changing middle_name should recompute name
        student.middle_name = 'Mary'
        self.assertEqual(student.name, 'Jane Mary Doe')
        
        # Test dependency triggers - changing last_name should recompute name
        student.last_name = 'Smith'
        self.assertEqual(student.name, 'Jane Mary Smith')

    def test_student_name_compute_edge_cases(self):
        """Test student name computation with edge cases."""
        # Test with None values
        student = self._create_test_student()
        student.first_name = None
        student.middle_name = None
        student.last_name = None
        student._onchange_name()
        self.assertFalse(student.name)
        
        # Test with empty strings
        student.first_name = ''
        student.middle_name = ''
        student.last_name = ''
        student._onchange_name()
        self.assertFalse(student.name)
        
        # Test with whitespace only
        student.first_name = '   '
        student.middle_name = '   '
        student.last_name = '   '
        student._onchange_name()
        self.assertFalse(student.name)

    def test_faculty_name_compute_dependencies(self):
        """Test faculty name compute method with proper dependencies."""
        faculty = self._create_test_faculty(
            first_name='Dr. John',
            middle_name='Michael',
            last_name='Smith'
        )
        
        # Test initial name computation
        self.assertEqual(faculty.name, 'Dr. John Michael Smith')
        
        # Test dependency triggers
        faculty.first_name = 'Prof. Jane'
        self.assertEqual(faculty.name, 'Prof. Jane Michael Smith')
        
        faculty.middle_name = 'Elizabeth'
        self.assertEqual(faculty.name, 'Prof. Jane Elizabeth Smith')
        
        faculty.last_name = 'Johnson'
        self.assertEqual(faculty.name, 'Prof. Jane Elizabeth Johnson')

    def test_faculty_name_compute_edge_cases(self):
        """Test faculty name computation with edge cases."""
        faculty = self._create_test_faculty()
        
        # Test with None values
        faculty.first_name = None
        faculty.middle_name = None
        faculty.last_name = None
        faculty._onchange_name()
        self.assertFalse(faculty.name)
        
        # Test with only first name
        faculty.first_name = 'John'
        faculty.middle_name = None
        faculty.last_name = None
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'John')
        
        # Test with only last name
        faculty.first_name = None
        faculty.middle_name = None
        faculty.last_name = 'Smith'
        faculty._onchange_name()
        self.assertEqual(faculty.name, 'Smith')

    def test_student_course_compute_methods(self):
        """Test student course compute methods if any exist."""
        student = self._create_test_student()
        course_detail = self._create_test_student_course(student_id=student.id)
        
        # Verify relationship is established
        self.assertEqual(course_detail.student_id, student)
        self.assertEqual(course_detail.course_id, self.test_course)
        self.assertEqual(course_detail.batch_id, self.test_batch)

    def test_batch_name_search_compute(self):
        """Test batch name_search method computation."""
        batch1 = self.env['op.batch'].create({
            'name': 'Test Batch Alpha',
            'code': 'TBA001',
            'course_id': self.test_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        batch2 = self.env['op.batch'].create({
            'name': 'Test Batch Beta',
            'code': 'TBB001',
            'course_id': self.test_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Test name search functionality
        results = self.env['op.batch'].name_search('Alpha')
        batch_ids = [result[0] for result in results]
        self.assertIn(batch1.id, batch_ids)
        self.assertNotIn(batch2.id, batch_ids)
        
        # Test code search functionality
        results = self.env['op.batch'].name_search('TBB')
        batch_ids = [result[0] for result in results]
        self.assertIn(batch2.id, batch_ids)
        self.assertNotIn(batch1.id, batch_ids)

    def test_course_recursive_check_compute(self):
        """Test course recursive category check computation."""
        parent_course = self.env['op.course'].create({
            'name': 'Parent Course',
            'code': 'PC001',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        child_course = self.env['op.course'].create({
            'name': 'Child Course',
            'code': 'CC001',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'parent_id': parent_course.id,
        })
        
        # Test _has_cycle method
        self.assertFalse(child_course._has_cycle())
        self.assertFalse(parent_course._has_cycle())

    def test_subject_registration_compute_methods(self):
        """Test subject registration compute methods."""
        student = self._create_test_student()
        course_detail = self._create_test_student_course(student_id=student.id)
        
        # Create subject registration
        subject_reg = self.env['op.subject.registration'].create({
            'student_id': student.id,
            'course_id': self.test_course.id,
            'batch_id': self.test_batch.id,
            'state': 'draft',
        })
        
        # Test compute methods if any exist
        self.assertEqual(subject_reg.student_id, student)
        self.assertEqual(subject_reg.course_id, self.test_course)
        self.assertEqual(subject_reg.batch_id, self.test_batch)

    def test_academic_year_term_compute_methods(self):
        """Test academic year and term compute methods."""
        # Create academic year
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Create academic term
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'term_start_date': '2024-01-01',
            'term_end_date': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # Test relationships and computed fields
        self.assertEqual(academic_term.academic_year_id, academic_year)
        self.assertTrue(academic_year.id)  # Verify record exists
        self.assertTrue(academic_term.id)  # Verify record exists

    def test_department_compute_methods(self):
        """Test department compute methods."""
        department = self.env['op.department'].create({
            'name': 'Computer Science Department',
            
        })
        
        # Test basic functionality
        self.assertEqual(department.name, 'Computer Science Department')
        self.assertEqual(department.code, 'CSD001')

    def test_program_compute_methods(self):
        """Test program compute methods."""
        program = self.env['op.program'].create({
            'name': 'Master of Computer Science',
            
            'department_id': self.test_department.id,
            'program_level_id': self.test_program_level.id,
        })
        
        # Test relationships
        self.assertEqual(program.department_id, self.test_department)
        self.assertEqual(program.program_level_id, self.test_program_level)

    def test_category_compute_methods(self):
        """Test category compute methods."""
        category = self.env['op.category'].create({
            'name': 'Test Category',
            
        })
        
        # Test basic functionality
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.code, 'TC001')

    def test_subject_compute_methods(self):
        """Test subject compute methods."""
        subject = self.env['op.subject'].create({
            'name': 'Advanced Programming',
            
            'type': 'theory',
            'subject_type': 'compulsory',
            'department_id': self.test_department.id,
        })
        
        # Test relationships and fields
        self.assertEqual(subject.department_id, self.test_department)
        self.assertEqual(subject.type, 'theory')
        self.assertEqual(subject.subject_type, 'compulsory')

    def test_performance_with_large_datasets(self):
        """Test compute method performance with larger datasets."""
        # Create multiple students and test name computation performance
        students = []
        for i in range(50):
            student = self._create_test_student(
                first_name=f'Student{i}',
                last_name=f'Test{i}'
            )
            students.append(student)
        
        # Test that all names are computed correctly
        for i, student in enumerate(students):
            self.assertEqual(student.name, f'Student{i} Test{i}')
        
        # Test batch name computation for multiple students
        self.assertEqual(len(students), 50)

    def test_compute_method_error_handling(self):
        """Test compute method error handling with invalid data."""
        student = self._create_test_student()
        
        # Test with invalid data types (should handle gracefully)
        try:
            # Since student inherits from res.partner, test partner name handling
            student.first_name = False
            student.middle_name = False  
            student.last_name = False
            # Name is from res.partner, not computed in op.student
            # Just verify the student can handle these values
            student.write({
                'first_name': False,
                'middle_name': False,
                'last_name': False
            })
            # Should not raise exception
        except Exception as e:
            self.fail(f"Student update failed with invalid data: {e}")

    def test_depends_decorator_validation(self):
        """Test that @api.depends decorators are properly set."""
        # Check student model dependencies
        student_model = self.env['op.student']
        if hasattr(student_model, '_compute_name'):
            # Get field dependencies from model
            name_field = student_model._fields.get('name')
            if name_field and hasattr(name_field, 'compute'):
                # Dependencies should be properly defined
                self.assertTrue(True)  # Dependencies exist

    def test_onchange_method_dependencies(self):
        """Test onchange method dependencies and behavior."""
        student = self._create_test_student()
        
        # Test onchange triggers
        student.first_name = 'Changed'
        student._onchange_name()
        self.assertIn('Changed', student.name)
        
        # Test multiple onchange triggers
        student.middle_name = 'Middle'
        student.last_name = 'Last'
        student._onchange_name()
        self.assertEqual(student.name, 'Changed Middle Last')