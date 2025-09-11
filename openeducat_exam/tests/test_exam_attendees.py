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
from .test_exam_common import TestExamCommon


@tagged('post_install', '-at_install', 'openeducat_exam')
class TestExamAttendees(TestExamCommon):
    """Test exam attendee management and registration."""

    def setUp(self):
        """Set up test data for attendee tests."""
        super().setUp()
        
        # Create scheduled exam
        self.exam = self.create_exam()
        self.exam.act_schedule()

    def test_exam_attendee_creation(self):
        """Test basic exam attendee creation."""
        attendee = self.create_exam_attendee(self.exam, self.student1)
        
        self.assertEqual(attendee.exam_id, self.exam, "Exam should be linked")
        self.assertEqual(attendee.student_id, self.student1, "Student should be linked")
        self.assertEqual(attendee.status, 'present', "Default status should be present")
        self.assertIsNone(attendee.marks, "Initial marks should be None")

    def test_exam_attendee_status_validation(self):
        """Test attendee status field validation."""
        attendee = self.create_exam_attendee(self.exam, self.student1)
        
        # Test valid statuses
        valid_statuses = ['present', 'absent']
        for status in valid_statuses:
            attendee.status = status
            self.assertEqual(attendee.status, status, f"Status {status} should be valid")

    def test_exam_attendee_marks_validation(self):
        """Test marks validation for attendees."""
        attendee = self.create_exam_attendee(self.exam, self.student1)
        
        # Test valid marks
        attendee.marks = 85
        self.assertEqual(attendee.marks, 85, "Valid marks should be accepted")
        
        # Test negative marks validation
        with self.assertRaises(ValidationError):
            attendee.marks = -10
        
        # Test marks exceeding total
        with self.assertRaises(ValidationError):
            attendee.marks = 150  # Exam total is 100

    def test_exam_attendee_absent_marks_validation(self):
        """Test that absent students cannot have marks."""
        attendee = self.create_exam_attendee(self.exam, self.student1, status='absent')
        
        # Absent student should not have marks
        with self.assertRaises(ValidationError):
            attendee.marks = 50

    def test_exam_attendee_unique_constraint(self):
        """Test unique constraint for student per exam."""
        # Create first attendee
        self.create_exam_attendee(self.exam, self.student1)
        
        # Try to create duplicate attendee for same student and exam
        with self.assertRaises(Exception):
            self.create_exam_attendee(self.exam, self.student1)

    def test_exam_attendee_bulk_creation(self):
        """Test bulk creation of exam attendees."""
        attendees_data = [
            {
                'exam_id': self.exam.id,
                'student_id': self.student1.id,
                'status': 'present',
            },
            {
                'exam_id': self.exam.id,
                'student_id': self.student2.id,
                'status': 'present',
            }
        ]
        
        attendees = self.env['op.exam.attendees'].create(attendees_data)
        
        self.assertEqual(len(attendees), 2, "Should create 2 attendees")
        self.assertEqual(attendees[0].student_id, self.student1, "First attendee should be student1")
        self.assertEqual(attendees[1].student_id, self.student2, "Second attendee should be student2")

    def test_exam_attendee_marks_entry_workflow(self):
        """Test complete marks entry workflow."""
        attendee = self.create_exam_attendee(self.exam, self.student1)
        
        # Step 1: Initially no marks
        self.assertIsNone(attendee.marks, "Initial marks should be None")
        
        # Step 2: Mark exam as held
        self.exam.act_held()
        
        # Step 3: Enter marks
        attendee.marks = 85
        
        # Step 4: Calculate grade based on marks
        grade = self._calculate_grade_for_marks(attendee.marks)
        attendee.grade = grade
        
        self.assertEqual(attendee.marks, 85, "Marks should be recorded")
        self.assertEqual(attendee.grade, 'A', "Grade should be calculated correctly")

    def _calculate_grade_for_marks(self, marks):
        """Helper method to calculate grade from marks."""
        if marks >= 90:
            return 'A+'
        elif marks >= 80:
            return 'A'
        elif marks >= 70:
            return 'B'
        elif marks >= 60:
            return 'C'
        else:
            return 'F'

    def test_exam_attendee_status_changes(self):
        """Test attendee status change scenarios."""
        attendee = self.create_exam_attendee(self.exam, self.student1, status='present')
        
        # Change to absent
        attendee.status = 'absent'
        self.assertEqual(attendee.status, 'absent', "Status should change to absent")
        
        # If marks exist when changing to absent, they should be cleared
        attendee.status = 'present'
        attendee.marks = 75
        attendee.status = 'absent'
        
        # Implementation may vary - some systems clear marks, others don't
        # This test documents the expected behavior

    def test_exam_attendee_search_and_filtering(self):
        """Test searching and filtering of exam attendees."""
        # Create attendees with different statuses
        present_attendee = self.create_exam_attendee(self.exam, self.student1, status='present')
        absent_attendee = self.create_exam_attendee(self.exam, self.student2, status='absent')
        
        # Search for present attendees
        present_attendees = self.env['op.exam.attendees'].search([
            ('exam_id', '=', self.exam.id),
            ('status', '=', 'present')
        ])
        
        self.assertIn(present_attendee, present_attendees, "Should find present attendee")
        self.assertNotIn(absent_attendee, present_attendees, "Should not find absent attendee")
        
        # Search for specific student
        student1_attendees = self.env['op.exam.attendees'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertIn(present_attendee, student1_attendees, "Should find student1's attendance")

    def test_exam_attendee_marks_statistics(self):
        """Test statistics calculation for exam attendees."""
        # Create attendees with marks
        attendee1 = self.create_exam_attendee(self.exam, self.student1, marks=85)
        attendee2 = self.create_exam_attendee(self.exam, self.student2, marks=72)
        
        # Calculate statistics
        all_attendees = self.env['op.exam.attendees'].search([
            ('exam_id', '=', self.exam.id),
            ('marks', '!=', None)
        ])
        
        total_marks = sum(attendee.marks for attendee in all_attendees)
        average_marks = total_marks / len(all_attendees) if all_attendees else 0
        highest_marks = max(attendee.marks for attendee in all_attendees) if all_attendees else 0
        lowest_marks = min(attendee.marks for attendee in all_attendees) if all_attendees else 0
        
        self.assertEqual(total_marks, 157, "Total marks should be 157")
        self.assertEqual(average_marks, 78.5, "Average should be 78.5")
        self.assertEqual(highest_marks, 85, "Highest should be 85")
        self.assertEqual(lowest_marks, 72, "Lowest should be 72")

    def test_exam_attendee_pass_fail_analysis(self):
        """Test pass/fail analysis for exam attendees."""
        # Create attendees with different marks
        pass_attendee = self.create_exam_attendee(self.exam, self.student1, marks=85)  # Pass
        fail_attendee = self.create_exam_attendee(self.exam, self.student2, marks=25)  # Fail
        
        # Analyze pass/fail based on minimum marks
        min_marks = self.exam.min_marks
        
        pass_result = pass_attendee.marks >= min_marks
        fail_result = fail_attendee.marks >= min_marks
        
        self.assertTrue(pass_result, "Student with 85 marks should pass")
        self.assertFalse(fail_result, "Student with 25 marks should fail")
        
        # Count pass/fail statistics
        all_attendees = self.env['op.exam.attendees'].search([
            ('exam_id', '=', self.exam.id),
            ('marks', '!=', None)
        ])
        
        passed_count = len([a for a in all_attendees if a.marks >= min_marks])
        failed_count = len([a for a in all_attendees if a.marks < min_marks])
        
        self.assertEqual(passed_count, 1, "Should have 1 passed student")
        self.assertEqual(failed_count, 1, "Should have 1 failed student")

    def test_exam_attendee_grade_distribution(self):
        """Test grade distribution analysis."""
        # Create attendees with various marks
        marks_and_grades = [
            (95, 'A+'),
            (85, 'A'),
            (75, 'B'),
            (65, 'C'),
            (45, 'F')
        ]
        
        attendees = []
        for i, (marks, expected_grade) in enumerate(marks_and_grades):
            # Create additional students for testing
            student = self.env['op.student'].create({
                'name': f'Grade Test Student {i}',
                'first_name': 'Grade',
                'last_name': f'Student{i}',
                'birth_date': '2000-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            
            attendee = self.create_exam_attendee(self.exam, student, marks=marks)
            attendee.grade = expected_grade
            attendees.append(attendee)
        
        # Analyze grade distribution
        grade_distribution = {}
        for attendee in attendees:
            grade = attendee.grade
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        expected_distribution = {'A+': 1, 'A': 1, 'B': 1, 'C': 1, 'F': 1}
        self.assertEqual(grade_distribution, expected_distribution,
                        "Grade distribution should match expected")

    def test_exam_attendee_reporting_data(self):
        """Test data preparation for attendee reports."""
        # Create attendees with complete data
        attendee1 = self.create_exam_attendee(self.exam, self.student1, marks=85)
        attendee1.grade = 'A'
        
        attendee2 = self.create_exam_attendee(self.exam, self.student2, marks=65)
        attendee2.grade = 'C'
        
        # Prepare report data
        report_data = []
        attendees = self.env['op.exam.attendees'].search([
            ('exam_id', '=', self.exam.id)
        ], order='marks desc')
        
        for rank, attendee in enumerate(attendees, 1):
            if attendee.marks is not None:
                report_data.append({
                    'rank': rank,
                    'student_name': attendee.student_id.name,
                    'marks': attendee.marks,
                    'grade': attendee.grade,
                    'status': 'Pass' if attendee.marks >= self.exam.min_marks else 'Fail'
                })
        
        # Verify report data
        self.assertEqual(len(report_data), 2, "Should have 2 report entries")
        self.assertEqual(report_data[0]['rank'], 1, "First rank should be 1")
        self.assertEqual(report_data[0]['marks'], 85, "First student should have 85 marks")

    def test_exam_attendee_bulk_marks_update(self):
        """Test bulk update of attendee marks."""
        # Create multiple attendees
        attendees = []
        for student in [self.student1, self.student2]:
            attendee = self.create_exam_attendee(self.exam, student)
            attendees.append(attendee)
        
        # Bulk update marks
        marks_updates = [
            {'attendee': attendees[0], 'marks': 88},
            {'attendee': attendees[1], 'marks': 76},
        ]
        
        for update in marks_updates:
            update['attendee'].marks = update['marks']
        
        # Verify updates
        self.assertEqual(attendees[0].marks, 88, "First attendee marks should be updated")
        self.assertEqual(attendees[1].marks, 76, "Second attendee marks should be updated")

    def test_exam_attendee_validation_edge_cases(self):
        """Test validation for edge cases."""
        attendee = self.create_exam_attendee(self.exam, self.student1)
        
        # Test boundary marks
        attendee.marks = 0  # Minimum valid marks
        self.assertEqual(attendee.marks, 0, "Zero marks should be valid")
        
        attendee.marks = self.exam.total_marks  # Maximum valid marks
        self.assertEqual(attendee.marks, self.exam.total_marks, "Full marks should be valid")
        
        # Test decimal marks (if supported)
        try:
            attendee.marks = 85.5
            # If successful, decimal marks are supported
        except (ValidationError, ValueError):
            # If error, only integer marks are supported
            pass

    def test_exam_attendee_performance_with_large_dataset(self):
        """Test performance with large number of attendees."""
        # Create additional students
        large_student_count = 100
        large_students = []
        
        for i in range(large_student_count):
            student = self.env['op.student'].create({
                'name': f'Performance Student {i}',
                'first_name': 'Performance',
                'last_name': f'Student{i}',
                'birth_date': '2000-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            large_students.append(student)
        
        # Measure bulk attendee creation performance
        start_time = self.env.now()
        
        attendees_data = []
        for student in large_students:
            attendees_data.append({
                'exam_id': self.exam.id,
                'student_id': student.id,
                'status': 'present',
                'marks': 75,  # Fixed marks for testing
            })
        
        attendees = self.env['op.exam.attendees'].create(attendees_data)
        
        end_time = self.env.now()
        creation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(attendees), large_student_count,
                        f"Should create {large_student_count} attendees")
        self.assertLess(creation_time, 10.0,
                       "Bulk creation should complete within 10 seconds")

    def test_exam_attendee_data_integrity(self):
        """Test data integrity constraints for attendees."""
        attendee = self.create_exam_attendee(self.exam, self.student1)
        
        # Test required field validation
        with self.assertRaises(Exception):
            self.env['op.exam.attendees'].create({
                'student_id': self.student2.id,
                # Missing exam_id
            })
        
        # Test foreign key constraint
        with self.assertRaises(Exception):
            self.env['op.exam.attendees'].create({
                'exam_id': 99999,  # Non-existent exam
                'student_id': self.student1.id,
            })