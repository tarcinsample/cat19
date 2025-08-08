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

from datetime import datetime, timedelta
from odoo.tests import tagged
from .test_assignment_common import TestAssignmentCommon


@tagged('post_install', '-at_install')
class TestAssignmentCompute(TestAssignmentCommon):
    """Test all compute methods for submission counts and grading statistics."""
    
    def test_assignment_submission_count_compute(self):
        """Test Task 3: Validate all compute methods for submission counts and grading statistics."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Initially no submissions
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 0)
        
        # Create first submission
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'First submission',
            'state': 'draft',
            'submission_date': datetime.now()
        })
        
        # Recompute and verify count
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        # Create second submission
        submission2 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student2.id,
            'description': 'Second submission',
            'state': 'draft',
            'submission_date': datetime.now()
        })
        
        # Recompute and verify count
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 2)
        
        # Test with submission deletion
        submission1.unlink()
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
    
    def test_compute_method_dependencies(self):
        """Test that compute methods have proper @api.depends decorators."""
        
        # Create assignment with submissions
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submissions
        submissions = []
        for i in range(3):
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': self.student1.id if i % 2 == 0 else self.student2.id,
                'description': f'Submission {i+1}',
                'state': 'draft',
                'submission_date': datetime.now()
            })
            submissions.append(submission)
        
        # Test that count is automatically computed when assignment_sub_line changes
        initial_count = assignment.assignment_sub_line_count
        self.assertEqual(initial_count, 3)
        
        # Add another submission - count should auto-update due to @api.depends
        new_submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'New submission',
            'state': 'draft',
            'submission_date': datetime.now()
        })
        
        # Count should be automatically updated
        self.assertEqual(assignment.assignment_sub_line_count, 4)
    
    def test_submission_statistics_by_state(self):
        """Test submission statistics grouped by state."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submissions in different states
        states_data = [
            ('draft', 2),
            ('submit', 3),
            ('accept', 2),
            ('reject', 1),
            ('change', 1)
        ]
        
        all_submissions = []
        for state, count in states_data:
            for i in range(count):
                submission = self.op_assignment_subline.create({
                    'assignment_id': assignment.id,
                    'student_id': self.student1.id if i % 2 == 0 else self.student2.id,
                    'description': f'Submission {state} {i+1}',
                    'state': state,
                    'submission_date': datetime.now()
                })
                all_submissions.append(submission)
        
        # Verify total count
        total_submissions = len(all_submissions)
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, total_submissions)
        
        # Test count by state using domain searches
        for state, expected_count in states_data:
            state_submissions = assignment.assignment_sub_line.filtered(lambda s: s.state == state)
            self.assertEqual(len(state_submissions), expected_count, 
                           f"Expected {expected_count} submissions in state {state}, got {len(state_submissions)}")
    
    def test_assignment_grading_statistics(self):
        """Test assignment grading statistics computation."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submissions with marks
        submissions_with_marks = [
            (self.student1.id, 85, 'accept'),
            (self.student2.id, 92, 'accept'),
        ]
        
        for student_id, marks, state in submissions_with_marks:
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student_id,
                'description': 'Graded submission',
                'state': state,
                'marks': marks
            })
        
        # Test statistics calculations
        accepted_submissions = assignment.assignment_sub_line.filtered(lambda s: s.state == 'accept')
        self.assertEqual(len(accepted_submissions), 2)
        
        # Calculate average marks
        total_marks = sum(accepted_submissions.mapped('marks'))
        average_marks = total_marks / len(accepted_submissions) if accepted_submissions else 0
        self.assertEqual(average_marks, 88.5)  # (85 + 92) / 2
    
    def test_performance_of_compute_methods(self):
        """Test performance of compute methods with large datasets."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create multiple students for performance testing
        students = []
        for i in range(10):
            partner = self.env['res.partner'].create({
                'name': f'Performance Test Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            students.append(student)
        
        # Create multiple submissions
        import time
        start_time = time.time()
        
        submissions = []
        for i, student in enumerate(students):
            for j in range(5):  # 5 submissions per student
                submission = self.op_assignment_subline.create({
                    'assignment_id': assignment.id,
                    'student_id': student.id,
                    'description': f'Performance test submission {i+1}-{j+1}',
                    'state': 'submit' if j % 2 == 0 else 'draft'
                })
                submissions.append(submission)
        
        # Test compute performance
        compute_start = time.time()
        assignment._compute_assignment_count_compute()
        compute_end = time.time()
        
        total_time = time.time() - start_time
        compute_time = compute_end - compute_start
        
        # Verify correct count
        expected_count = len(students) * 5  # 10 students * 5 submissions each
        self.assertEqual(assignment.assignment_sub_line_count, expected_count)
        
        # Performance should be reasonable (less than 1 second for this dataset)
        self.assertLess(compute_time, 1.0, "Compute method taking too long")
    
    def test_compute_with_empty_datasets(self):
        """Test compute methods with empty or null datasets."""
        
        # Create assignment without submissions
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test compute with no submissions
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 0)
        
        # Test compute after all submissions are deleted
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Temporary submission'
        })
        
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        # Delete submission
        submission.unlink()
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 0)
    
    def test_compute_method_triggers(self):
        """Test that compute methods are triggered correctly."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Initial state
        self.assertEqual(assignment.assignment_sub_line_count, 0)
        
        # Create submission - should trigger compute automatically
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Auto-trigger test'
        })
        
        # Count should be updated automatically due to @api.depends
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        # Modify submission (should not affect count)
        submission1.write({'description': 'Modified description'})
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        # Delete submission - should trigger compute automatically
        submission1.unlink()
        self.assertEqual(assignment.assignment_sub_line_count, 0)
    
    def test_multi_assignment_compute_isolation(self):
        """Test that compute methods work correctly with multiple assignments."""
        
        # Create multiple assignments
        assignments = []
        for i in range(3):
            grading_assignment = self.grading_assignment.create({
                'name': f'Test Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now(),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data['grading_assignment_id'] = grading_assignment.id
            assignment = self.op_assignment.create(assignment_data)
            assignments.append(assignment)
        
        # Create different numbers of submissions for each assignment
        submission_counts = [2, 3, 1]
        
        for i, (assignment, count) in enumerate(zip(assignments, submission_counts)):
            for j in range(count):
                self.op_assignment_subline.create({
                    'assignment_id': assignment.id,
                    'student_id': self.student1.id if j % 2 == 0 else self.student2.id,
                    'description': f'Assignment {i+1} Submission {j+1}'
                })
        
        # Verify each assignment has correct count
        for assignment, expected_count in zip(assignments, submission_counts):
            assignment._compute_assignment_count_compute()
            self.assertEqual(assignment.assignment_sub_line_count, expected_count)
    
    def test_compute_with_submission_state_changes(self):
        """Test compute methods when submission states change."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'State change test'
        })
        
        # Initial count
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        # Change submission state - count should remain the same
        submission.act_submit()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        submission.act_accept()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        submission.act_reject()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        # Count only changes when submissions are added/removed, not state changes