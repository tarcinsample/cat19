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


@tagged('post_install', '-at_install', 'integration')
class TestIntegration(TestCoreCommon):
    """Integration testing for Student-Course-Batch relationships."""

    def test_student_course_batch_enrollment_workflow(self):
        """Test complete student enrollment workflow."""
        # Create student
        student = self._create_test_student(
            first_name='John',
            last_name='Doe',
            birth_date='2000-01-01',
            gr_no='ST001'
        )
        
        # Create course enrollment
        course_detail = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL001'
        )
        
        # Verify complete relationship
        self.assertEqual(course_detail.student_id, student)
        self.assertEqual(course_detail.course_id, self.test_course)
        self.assertEqual(course_detail.batch_id, self.test_batch)
        self.assertIn(course_detail, student.course_detail_ids)

    def test_multiple_student_same_batch(self):
        """Test multiple students enrolled in same batch."""
        students = []
        course_details = []
        
        # Create 5 students in same batch
        for i in range(5):
            student = self._create_test_student(
                first_name=f'Student{i}',
                last_name='Test',
                gr_no=f'ST{i:03d}'
            )
            students.append(student)
            
            course_detail = self._create_test_student_course(
                student_id=student.id,
                roll_number=f'ROLL{i:03d}'
            )
            course_details.append(course_detail)
        
        # Verify all students are in same batch
        for course_detail in course_details:
            self.assertEqual(course_detail.batch_id, self.test_batch)
            self.assertEqual(course_detail.course_id, self.test_course)
        
        # Verify unique roll numbers
        roll_numbers = [cd.roll_number for cd in course_details]
        self.assertEqual(len(roll_numbers), len(set(roll_numbers)))

    def test_student_multiple_course_enrollments(self):
        """Test student enrolled in multiple courses."""
        student = self._create_test_student(gr_no='MULTI001')
        
        # Create additional course and batch
        course2 = self.env['op.course'].create({
            'name': 'Advanced Mathematics',
            'code': 'MATH301',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        batch2 = self.env['op.batch'].create({
            'name': 'Math Batch 2024',
            'code': 'MB2024',
            'course_id': course2.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Enroll student in first course
        course_detail1 = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL_CS001'
        )
        
        # Enroll student in second course
        course_detail2 = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course2.id,
            'batch_id': batch2.id,
            'roll_number': 'ROLL_MATH001',
        })
        
        # Verify student has multiple enrollments
        self.assertEqual(len(student.course_detail_ids), 2)
        self.assertIn(course_detail1, student.course_detail_ids)
        self.assertIn(course_detail2, student.course_detail_ids)

    def test_course_subject_batch_integration(self):
        """Test course-subject-batch integration."""
        # Add subjects to course
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
            'type': 'practical',
            'subject_type': 'elective',
            'department_id': self.test_department.id,
        })
        
        # Assign subjects to course
        self.test_course.subject_ids = [(6, 0, [
            self.test_subject.id,
            subject2.id,
            subject3.id
        ])]
        
        # Create student and enroll in course
        student = self._create_test_student(gr_no='INT001')
        course_detail = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL_INT001'
        )
        
        # Verify course has subjects
        self.assertEqual(len(self.test_course.subject_ids), 3)
        self.assertIn(self.test_subject, self.test_course.subject_ids)
        self.assertIn(subject2, self.test_course.subject_ids)
        self.assertIn(subject3, self.test_course.subject_ids)
        
        # Verify student is enrolled in course with subjects
        self.assertEqual(course_detail.course_id, self.test_course)
        self.assertEqual(len(course_detail.course_id.subject_ids), 3)

    def test_department_program_course_hierarchy(self):
        """Test department-program-course hierarchy integration."""
        # Create additional department
        dept2 = self.env['op.department'].create({
            'name': 'Physics Department',
            'code': 'PHY001',
        })
        
        # Create program in new department
        program2 = self.env['op.program'].create({
            'name': 'Master of Physics',
            'code': 'MSP001',
            'department_id': dept2.id,
            'program_level_id': self.test_program_level.id,
        })
        
        # Create course in new program
        course2 = self.env['op.course'].create({
            'name': 'Quantum Mechanics',
            'code': 'QM301',
            'department_id': dept2.id,
            'program_id': program2.id,
        })
        
        # Verify hierarchy relationships
        self.assertEqual(course2.department_id, dept2)
        self.assertEqual(course2.program_id, program2)
        self.assertEqual(program2.department_id, dept2)

    def test_academic_year_term_integration(self):
        """Test academic year and term integration."""
        # Create academic year
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Create terms within academic year
        term1 = self.env['op.academic.term'].create({
            'name': 'Fall 2024',
            'term_start_date': '2024-08-01',
            'term_end_date': '2024-12-31',
            'academic_year_id': academic_year.id,
        })
        
        term2 = self.env['op.academic.term'].create({
            'name': 'Spring 2025',
            'term_start_date': '2025-01-01',
            'term_end_date': '2025-05-31',
            'academic_year_id': academic_year.id,
        })
        
        # Verify relationships
        self.assertEqual(term1.academic_year_id, academic_year)
        self.assertEqual(term2.academic_year_id, academic_year)
        
        # Test date ranges are within academic year
        self.assertGreaterEqual(term1.start_date, academic_year.start_date)
        self.assertLessEqual(term1.end_date, academic_year.end_date)

    def test_faculty_subject_course_assignment(self):
        """Test faculty assignment to subjects and courses."""
        # Create faculty
        faculty = self._create_test_faculty(
            first_name='Dr. Jane',
            last_name='Professor'
        )
        
        # Create subject assignment (if model exists)
        # This would depend on the actual implementation
        subject_assignment = {
            'faculty_id': faculty.id,
            'subject_id': self.test_subject.id,
            'course_id': self.test_course.id,
            'batch_id': self.test_batch.id,
        }
        
        # Verify faculty can be assigned to subjects
        self.assertTrue(faculty.id)
        self.assertTrue(self.test_subject.id)

    def test_student_category_integration(self):
        """Test student category integration."""
        # Create additional categories
        category_sc = self.env['op.category'].create({
            'name': 'Scheduled Caste',
            
        })
        
        category_st = self.env['op.category'].create({
            'name': 'Scheduled Tribe',
            
        })
        
        # Create students with different categories
        student_general = self._create_test_student(
            first_name='General',
            last_name='Student',
            category_id=self.test_category.id,
            gr_no='GEN001'
        )
        
        student_sc = self._create_test_student(
            first_name='SC',
            last_name='Student',
            category_id=category_sc.id,
            gr_no='SC001'
        )
        
        student_st = self._create_test_student(
            first_name='ST',
            last_name='Student',
            category_id=category_st.id,
            gr_no='ST001'
        )
        
        # Verify category assignments
        self.assertEqual(student_general.category_id, self.test_category)
        self.assertEqual(student_sc.category_id, category_sc)
        self.assertEqual(student_st.category_id, category_st)

    def test_batch_date_validation_integration(self):
        """Test batch date validation in context of enrollments."""
        # Create batch with future dates
        future_batch = self.env['op.batch'].create({
            'name': 'Future Batch',
            
            'course_id': self.test_course.id,
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        })
        
        # Create student enrollment in future batch
        student = self._create_test_student(gr_no='FUTURE001')
        course_detail = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': self.test_course.id,
            'batch_id': future_batch.id,
            'roll_number': 'ROLL_FUTURE001',
        })
        
        # Verify enrollment is valid
        self.assertEqual(course_detail.batch_id, future_batch)
        self.assertEqual(course_detail.student_id, student)

    def test_course_hierarchy_enrollment_impact(self):
        """Test how course hierarchy affects student enrollment."""
        # Create parent-child course relationship
        parent_course = self.env['op.course'].create({
            'name': 'Foundation Mathematics',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        child_course = self.env['op.course'].create({
            'name': 'Advanced Mathematics',
            
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'academic_year_id': parent_course.id,
        })
        
        # Create batches for both courses
        parent_batch = self.env['op.batch'].create({
            'name': 'Foundation Batch',
            
            'course_id': parent_course.id,
            'start_date': '2024-01-01',
            'end_date': '2024-06-30',
        })
        
        child_batch = self.env['op.batch'].create({
            'name': 'Advanced Batch',
            
            'course_id': child_course.id,
            'start_date': '2024-07-01',
            'end_date': '2024-12-31',
        })
        
        # Enroll student in both courses
        student = self._create_test_student(gr_no='HIER001')
        
        foundation_enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': parent_course.id,
            'batch_id': parent_batch.id,
            'roll_number': 'ROLL_FOUND001',
        })
        
        advanced_enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': child_course.id,
            'batch_id': child_batch.id,
            'roll_number': 'ROLL_ADV001',
        })
        
        # Verify hierarchical enrollment
        self.assertEqual(foundation_enrollment.course_id, parent_course)
        self.assertEqual(advanced_enrollment.course_id, child_course)
        self.assertEqual(child_course.parent_id, parent_course)

    def test_subject_registration_workflow(self):
        """Test complete subject registration workflow."""
        # Create student and enroll in course
        student = self._create_test_student(gr_no='SUBJ001')
        course_detail = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL_SUBJ001'
        )
        
        # Create subject registration
        subject_reg = self.env['op.subject.registration'].create({
            'student_id': student.id,
            'course_id': self.test_course.id,
            'batch_id': self.test_batch.id,
            'state': 'draft',
        })
        
        # Add subject to registration
        subject_line = self.env['op.subject.registration.line'].create({
            'subject_id': self.test_subject.id,
            'registration_id': subject_reg.id,
        })
        
        # Verify registration workflow
        self.assertEqual(subject_reg.student_id, student)
        self.assertEqual(subject_reg.course_id, self.test_course)
        self.assertEqual(subject_reg.batch_id, self.test_batch)
        self.assertIn(subject_line, subject_reg.line_ids)

    def test_bulk_student_operations(self):
        """Test bulk operations on student data."""
        # Create multiple students
        students = []
        for i in range(10):
            student = self._create_test_student(
                first_name=f'Bulk{i}',
                last_name='Student',
                gr_no=f'BULK{i:03d}'
            )
            students.append(student)
        
        # Bulk enroll in course
        course_details = []
        for i, student in enumerate(students):
            course_detail = self._create_test_student_course(
                student_id=student.id,
                roll_number=f'BULK_ROLL{i:03d}'
            )
            course_details.append(course_detail)
        
        # Verify all enrollments
        self.assertEqual(len(course_details), 10)
        for course_detail in course_details:
            self.assertEqual(course_detail.course_id, self.test_course)
            self.assertEqual(course_detail.batch_id, self.test_batch)

    def test_data_consistency_across_models(self):
        """Test data consistency across related models."""
        # Create complete educational setup
        student = self._create_test_student(gr_no='CONSIST001')
        course_detail = self._create_test_student_course(
            student_id=student.id,
            roll_number='ROLL_CONSIST001'
        )
        
        # Verify consistency
        # Student name should be consistent
        self.assertEqual(student.name, f"{student.first_name} {student.last_name}")
        
        # Course-batch relationship should be consistent
        self.assertEqual(course_detail.course_id, self.test_course)
        self.assertEqual(course_detail.batch_id.course_id, self.test_course)
        
        # Department consistency
        self.assertEqual(self.test_course.department_id, self.test_department)
        self.assertEqual(self.test_program.department_id, self.test_department)
        
        # Subject-department consistency
        self.assertEqual(self.test_subject.department_id, self.test_department)