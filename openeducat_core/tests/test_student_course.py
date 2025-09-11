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
from psycopg2 import IntegrityError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'student_course')
class TestStudentCourse(TestCoreCommon):
    """Comprehensive tests for op.student.course model."""

    def test_student_course_creation_valid_data(self):
        """Test student course creation with valid data."""
        student = self._create_test_student()
        
        student_course = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL001'
        )
        
        self.assertEqual(student_course.student_id, student)
        self.assertEqual(student_course.course_id, self.test_course)
        self.assertEqual(student_course.batch_id, self.test_batch)
        self.assertEqual(student_course.roll_number, 'ROLL001')
        self.assertEqual(student_course.state, 'running')

    def test_student_course_roll_number_uniqueness(self):
        """Test roll number uniqueness per batch constraint."""
        student1 = self._create_test_student(first_name='Student1')
        student2 = self._create_test_student(first_name='Student2')
        
        # Create first enrollment
        self._create_test_student_course(
            student_id=student1.id,
            roll_number='ROLLDUP001'
        )
        
        # Try to create second enrollment with same roll number in same batch
        with self.assertRaises(IntegrityError):
            self._create_test_student_course(
                student_id=student2.id,
                roll_number='ROLLDUP001'  # Duplicate roll number
            )

    def test_student_course_student_uniqueness_per_batch(self):
        """Test student uniqueness per course and batch constraint."""
        student = self._create_test_student()
        
        # Create first enrollment
        self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLLUNIQ001'
        )
        
        # Try to enroll same student in same course/batch
        with self.assertRaises(IntegrityError):
            self._create_test_student_course(
                student_id=student.id,  # Same student
                roll_number='ROLLUNIQ002'   # Different roll number
            )

    def test_student_course_different_batches_allowed(self):
        """Test same student can enroll in different batches."""
        student = self._create_test_student()
        
        # Create second batch
        batch2 = self.env['op.batch'].create({
            'name': 'Batch 2025',
            'code': 'B2025',
            'course_id': self.test_course.id,
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        })
        
        # Enroll in first batch
        enrollment1 = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLLBATCH001'
        )
        
        # Enroll in second batch (should work)
        enrollment2 = self._create_test_student_course(
            student_id=student.id,
            batch_id=batch2.id,
            roll_number='ROLLBATCH001'  # Same roll number in different batch is OK
        )
        
        self.assertEqual(enrollment1.batch_id, self.test_batch)
        self.assertEqual(enrollment2.batch_id, batch2)

    def test_student_course_state_transitions(self):
        """Test student course state management."""
        student = self._create_test_student()
        student_course = self._create_test_student_course(student_id=student.id)
        
        # Default state should be running
        self.assertEqual(student_course.state, 'running')
        
        # Change to finished
        student_course.state = 'finished'
        self.assertEqual(student_course.state, 'finished')

    def test_student_course_subject_assignment(self):
        """Test subject assignment to student course."""
        student = self._create_test_student()
        student_course = self._create_test_student_course(student_id=student.id)
        
        # Assign subjects
        student_course.subject_ids = [(6, 0, [self.test_subject.id])]
        
        self.assertIn(self.test_subject, student_course.subject_ids)

    def test_student_course_academic_year_term(self):
        """Test academic year and term assignment."""
        # Create academic year
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-06-01',
            'end_date': '2025-05-31',
        })
        
        # Create academic term
        academic_term = self.env['op.academic.term'].create({
            'name': 'Semester 1',
            'term_start_date': '2024-06-01', 
            'term_end_date': '2024-11-30',
            'academic_year_id': academic_year.id,
        })
        
        student = self._create_test_student()
        student_course = self._create_test_student_course(
            student_id=student.id,
            academic_years_id=academic_year.id,
            academic_term_id=academic_term.id
        )
        
        self.assertEqual(student_course.academic_years_id, academic_year)
        self.assertEqual(student_course.academic_term_id, academic_term)

    def test_student_course_get_import_templates(self):
        """Test get_import_templates method."""
        student_course_model = self.env['op.student.course']
        templates = student_course_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 1)
        
        template = templates[0]
        self.assertIn('label', template)
        self.assertIn('template', template)
        self.assertEqual(template['template'], '/openeducat_core/static/xls/op_student_course.xls')

    def test_student_course_tracking_fields(self):
        """Test that tracking fields are properly configured."""
        student = self._create_test_student()
        student_course = self._create_test_student_course(student_id=student.id)
        
        # Test field help texts exist
        field_info = self.env['op.student.course'].fields_get()
        
        self.assertIn('help', field_info['student_id'])
        self.assertIn('help', field_info['course_id'])
        self.assertIn('help', field_info['batch_id'])
        self.assertIn('help', field_info['roll_number'])

    def test_student_course_name_display(self):
        """Test student course display name functionality."""
        student = self._create_test_student(first_name='John', last_name='Doe')
        student_course = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL001'
        )
        
        # Display name should include relevant information
        display_name = student_course.display_name
        self.assertTrue(display_name)

    def test_student_course_multiple_subjects(self):
        """Test enrollment with multiple subjects."""
        # Create additional subjects
        subject2 = self.env['op.subject'].create({
            'name': 'Physics',
            'code': 'PHY101',
            'type': 'theory',
            'subject_type': 'compulsory',
            'department_id': self.test_department.id,
        })
        
        subject3 = self.env['op.subject'].create({
            'name': 'Chemistry',
            'code': 'CHEM101',
            'type': 'theory',
            'subject_type': 'elective',
            'department_id': self.test_department.id,
        })
        
        student = self._create_test_student()
        student_course = self._create_test_student_course(student_id=student.id)
        
        # Assign multiple subjects
        student_course.subject_ids = [(6, 0, [self.test_subject.id, subject2.id, subject3.id])]
        
        self.assertEqual(len(student_course.subject_ids), 3)
        self.assertIn(self.test_subject, student_course.subject_ids)
        self.assertIn(subject2, student_course.subject_ids)
        self.assertIn(subject3, student_course.subject_ids)

    def test_student_course_batch_course_relationship(self):
        """Test that batch and course relationship is maintained."""
        student = self._create_test_student()
        student_course = self._create_test_student_course(student_id=student.id)
        
        # Batch should belong to the same course
        self.assertEqual(student_course.batch_id.course_id, student_course.course_id)

    def test_student_course_sql_constraints_names(self):
        """Test SQL constraint names are descriptive."""
        model = self.env['op.student.course']
        constraints = model._sql_constraints
        
        # Check constraint names are descriptive
        constraint_names = [constraint[0] for constraint in constraints]
        
        self.assertIn('unique_roll_number_per_batch', constraint_names)
        self.assertIn('unique_student_per_course_batch', constraint_names)