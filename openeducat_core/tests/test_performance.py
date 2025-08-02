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

import time
from odoo.tests import tagged
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'performance')
class TestPerformance(TestCoreCommon):
    """Performance testing for bulk student/faculty operations."""

    def test_bulk_student_creation_performance(self):
        """Test performance of creating multiple students."""
        start_time = time.time()
        
        students = []
        for i in range(100):
            student = self._create_test_student(
                first_name=f'Student{i}',
                last_name=f'Test{i}',
                gr_no=f'PERF{i:04d}'
            )
            students.append(student)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create 100 students in reasonable time (< 30 seconds)
        self.assertLess(duration, 30, 
                       f"Creating 100 students took {duration:.2f} seconds")
        self.assertEqual(len(students), 100)

    def test_bulk_faculty_creation_performance(self):
        """Test performance of creating multiple faculty members."""
        start_time = time.time()
        
        faculty_members = []
        for i in range(50):
            faculty = self._create_test_faculty(
                first_name=f'Faculty{i}',
                last_name=f'Test{i}'
            )
            faculty_members.append(faculty)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create 50 faculty members in reasonable time (< 15 seconds)
        self.assertLess(duration, 15, 
                       f"Creating 50 faculty members took {duration:.2f} seconds")
        self.assertEqual(len(faculty_members), 50)

    def test_bulk_course_enrollment_performance(self):
        """Test performance of bulk course enrollments."""
        # Create students first
        students = []
        for i in range(50):
            student = self._create_test_student(
                first_name=f'Enroll{i}',
                last_name='Test',
                gr_no=f'ENROLL{i:03d}'
            )
            students.append(student)
        
        # Time the enrollment process
        start_time = time.time()
        
        course_details = []
        for i, student in enumerate(students):
            course_detail = self._create_test_student_course(
                student_id=student.id,
                roll_number=f'ROLL{i:04d}'
            )
            course_details.append(course_detail)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should enroll 50 students in reasonable time (< 10 seconds)
        self.assertLess(duration, 10, 
                       f"Enrolling 50 students took {duration:.2f} seconds")
        self.assertEqual(len(course_details), 50)

    def test_student_search_performance(self):
        """Test performance of student search operations."""
        # Create test data
        for i in range(100):
            self._create_test_student(
                first_name=f'Search{i}',
                last_name='Student',
                gr_no=f'SEARCH{i:03d}'
            )
        
        # Test name search performance
        start_time = time.time()
        results = self.student_model.search([('name', 'ilike', 'Search')])
        end_time = time.time()
        duration = end_time - start_time
        
        # Should search through 100+ students quickly (< 2 seconds)
        self.assertLess(duration, 2, 
                       f"Searching students took {duration:.2f} seconds")
        self.assertGreaterEqual(len(results), 100)

    def test_course_search_performance(self):
        """Test performance of course search operations."""
        # Create test courses
        for i in range(50):
            self.env['op.course'].create({
                'name': f'Performance Course {i}',
                'code': f'PERF{i:03d}',
                'department_id': self.test_department.id,
                'program_id': self.test_program.id,
            })
        
        # Test course search performance
        start_time = time.time()
        results = self.course_model.search([('name', 'ilike', 'Performance')])
        end_time = time.time()
        duration = end_time - start_time
        
        # Should search through 50+ courses quickly (< 1 second)
        self.assertLess(duration, 1, 
                       f"Searching courses took {duration:.2f} seconds")
        self.assertGreaterEqual(len(results), 50)

    def test_batch_search_performance(self):
        """Test performance of batch search operations."""
        # Create test batches
        for i in range(30):
            self.env['op.batch'].create({
                'name': f'Performance Batch {i}',
                'code': f'PB{i:03d}',
                'course_id': self.test_course.id,
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
            })
        
        # Test batch search performance
        start_time = time.time()
        results = self.batch_model.search([('name', 'ilike', 'Performance')])
        end_time = time.time()
        duration = end_time - start_time
        
        # Should search through 30+ batches quickly (< 1 second)
        self.assertLess(duration, 1, 
                       f"Searching batches took {duration:.2f} seconds")
        self.assertGreaterEqual(len(results), 30)

    def test_name_computation_performance(self):
        """Test performance of name computation for large datasets."""
        # Create students with various name combinations
        students = []
        start_time = time.time()
        
        for i in range(200):
            student = self._create_test_student(
                first_name=f'First{i}',
                middle_name=f'Middle{i}' if i % 3 == 0 else None,
                last_name=f'Last{i}',
                gr_no=f'NAME{i:04d}'
            )
            students.append(student)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle name computation for 200 students efficiently
        self.assertLess(duration, 20, 
                       f"Name computation for 200 students took {duration:.2f} seconds")
        
        # Verify names are computed correctly
        for i, student in enumerate(students):
            if i % 3 == 0:
                expected_name = f'First{i} Middle{i} Last{i}'
            else:
                expected_name = f'First{i} Last{i}'
            self.assertEqual(student.name, expected_name)

    def test_constraint_validation_performance(self):
        """Test performance of constraint validation on bulk operations."""
        # Test birth date constraint performance
        start_time = time.time()
        
        students = []
        for i in range(100):
            student = self._create_test_student(
                first_name=f'Constraint{i}',
                last_name='Test',
                birth_date='2000-01-01',  # Valid date
                gr_no=f'CONST{i:04d}'
            )
            students.append(student)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should validate constraints for 100 students efficiently
        self.assertLess(duration, 15, 
                       f"Constraint validation for 100 students took {duration:.2f} seconds")

    def test_relationship_loading_performance(self):
        """Test performance of loading relationships."""
        # Create students with course enrollments
        students = []
        for i in range(50):
            student = self._create_test_student(
                first_name=f'Relation{i}',
                last_name='Test',
                gr_no=f'REL{i:03d}'
            )
            students.append(student)
            
            # Create course enrollment
            self._create_test_student_course(
                student_id=student.id,
                roll_number=f'REL_ROLL{i:03d}'
            )
        
        # Test loading relationships performance
        start_time = time.time()
        
        for student in students:
            # Access relationship (should trigger loading)
            course_details = student.course_detail_ids
            self.assertGreater(len(course_details), 0)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should load relationships efficiently
        self.assertLess(duration, 5, 
                       f"Loading relationships for 50 students took {duration:.2f} seconds")

    def test_bulk_update_performance(self):
        """Test performance of bulk update operations."""
        # Create students
        students = []
        for i in range(100):
            student = self._create_test_student(
                first_name=f'BulkUpdate{i}',
                last_name='Test',
                gr_no=f'BULK{i:03d}'
            )
            students.append(student)
        
        # Test bulk update performance
        start_time = time.time()
        
        # Update all students' birth date
        for student in students:
            student.birth_date = '1999-01-01'
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should update 100 students efficiently
        self.assertLess(duration, 10, 
                       f"Bulk update of 100 students took {duration:.2f} seconds")

    def test_complex_query_performance(self):
        """Test performance of complex queries."""
        # Create diverse test data
        categories = []
        for i in range(5):
            category = self.env['op.category'].create({
                'name': f'Category {i}',
                'code': f'CAT{i}',
            })
            categories.append(category)
        
        # Create students in different categories
        for i in range(100):
            student = self._create_test_student(
                first_name=f'Complex{i}',
                last_name='Query',
                category_id=categories[i % 5].id,
                gr_no=f'COMPLEX{i:03d}'
            )
        
        # Test complex query performance
        start_time = time.time()
        
        # Complex search with joins
        results = self.student_model.search([
            ('name', 'ilike', 'Complex'),
            ('category_id.name', 'ilike', 'Category'),
            ('birth_date', '!=', False)
        ])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle complex queries efficiently
        self.assertLess(duration, 3, 
                       f"Complex query took {duration:.2f} seconds")
        self.assertGreaterEqual(len(results), 100)

    def test_import_template_performance(self):
        """Test performance of import template operations."""
        start_time = time.time()
        
        # Test import template retrieval for multiple models
        student_templates = self.student_model.get_import_templates()
        course_templates = self.course_model.get_import_templates()
        batch_templates = self.batch_model.get_import_templates()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should retrieve templates quickly
        self.assertLess(duration, 1, 
                       f"Import template retrieval took {duration:.2f} seconds")
        
        # Verify templates exist
        self.assertGreater(len(student_templates), 0)
        self.assertGreater(len(course_templates), 0)
        self.assertGreater(len(batch_templates), 0)

    def test_user_creation_performance(self):
        """Test performance of user creation for students."""
        # Create students
        students = []
        for i in range(20):
            student = self._create_test_student(
                first_name=f'UserTest{i}',
                last_name='Student',
                email=f'usertest{i}@example.com',
                gr_no=f'USER{i:03d}'
            )
            student.partner_id.email = f'usertest{i}@example.com'
            students.append(student)
        
        # Test user creation performance
        start_time = time.time()
        
        for student in students:
            student.create_student_user()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create users efficiently
        self.assertLess(duration, 10, 
                       f"Creating users for 20 students took {duration:.2f} seconds")
        
        # Verify users were created
        users_created = sum(1 for student in students if student.user_id)
        self.assertEqual(users_created, 20)

    def test_memory_usage_large_dataset(self):
        """Test memory usage with large datasets."""
        # This is a basic test - in production, you might want more sophisticated memory monitoring
        
        # Create a significant amount of data
        students = []
        for i in range(500):
            student = self._create_test_student(
                first_name=f'Memory{i}',
                last_name='Test',
                gr_no=f'MEM{i:04d}'
            )
            students.append(student)
        
        # Verify all students were created successfully
        self.assertEqual(len(students), 500)
        
        # Test that we can still perform operations efficiently
        start_time = time.time()
        search_results = self.student_model.search([('name', 'ilike', 'Memory')])
        end_time = time.time()
        
        self.assertLessEqual(end_time - start_time, 3)
        self.assertGreaterEqual(len(search_results), 500)

    def test_concurrent_operation_simulation(self):
        """Simulate concurrent operations for performance testing."""
        # This simulates what might happen with multiple users
        
        start_time = time.time()
        
        # Simulate multiple operations happening "concurrently"
        for i in range(10):
            # Create student
            student = self._create_test_student(
                first_name=f'Concurrent{i}',
                last_name='Test',
                gr_no=f'CONC{i:03d}'
            )
            
            # Enroll in course
            course_detail = self._create_test_student_course(
                student_id=student.id,
                roll_number=f'CONC_ROLL{i:03d}'
            )
            
            # Search operation
            search_results = self.student_model.search([('name', 'ilike', 'Concurrent')])
            
            # Update operation
            student.first_name = f'Updated{i}'
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle simulated concurrent operations efficiently
        self.assertLess(duration, 5, 
                       f"Simulated concurrent operations took {duration:.2f} seconds")