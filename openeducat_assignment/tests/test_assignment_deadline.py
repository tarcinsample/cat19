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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_assignment_common import TestAssignmentCommon


@tagged('post_install', '-at_install')
class TestAssignmentDeadline(TestAssignmentCommon):
    """Test assignment deadline management and late submission handling."""
    
    def test_assignment_deadline_validation(self):
        """Test Task 4: Test assignment deadline management and late submission handling."""
        
        # Test valid deadline (future date)
        future_date = datetime.now() + timedelta(days=7)
        grading_assignment = self.grading_assignment.create({
            'name': 'Valid Deadline Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': future_date
        })
        
        assignment = self.op_assignment.create(assignment_data)
        self.assertTrue(assignment.id)
        self.assertEqual(assignment.submission_date, future_date)
    
    def test_invalid_deadline_before_issue_date(self):
        """Test assignment with submission date before issue date."""
        
        # Test invalid deadline (before issue date)
        issue_date = datetime.now()
        invalid_submission_date = issue_date - timedelta(days=1)
        
        grading_assignment = self.grading_assignment.create({
            'name': 'Invalid Deadline Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': issue_date,
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': invalid_submission_date
        })
        
        with self.assertRaises(ValidationError) as context:
            self.op_assignment.create(assignment_data)
        
        self.assertIn('Submission Date', str(context.exception))
        self.assertIn('Issue Date', str(context.exception))
    
    def test_deadline_constraint_on_update(self):
        """Test deadline validation when updating existing assignment."""
        
        # Create valid assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Try to update with invalid deadline
        with self.assertRaises(ValidationError):
            assignment.write({
                'submission_date': assignment.issued_date - timedelta(days=1)
            })
    
    def test_late_submission_scenarios(self):
        """Test various late submission scenarios."""
        
        # Create assignment with past deadline
        past_deadline = datetime.now() - timedelta(days=1)
        grading_assignment = self.grading_assignment.create({
            'name': 'Past Deadline Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now() - timedelta(days=7),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': past_deadline
        })
        
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create late submission (submission date after deadline)
        late_submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'This is a late submission',
            'submission_date': datetime.now()  # After deadline
        })
        
        # Verify submission can be created (system allows late submissions)
        self.assertTrue(late_submission.id)
        self.assertEqual(late_submission.state, 'draft')
        
        # Faculty can still process late submissions
        late_submission.act_submit()
        self.assertEqual(late_submission.state, 'submit')
    
    def test_on_time_submission_scenarios(self):
        """Test on-time submission scenarios."""
        
        # Create assignment with future deadline
        future_deadline = datetime.now() + timedelta(days=7)
        grading_assignment = self.grading_assignment.create({
            'name': 'Future Deadline Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': future_deadline
        })
        
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create on-time submission
        on_time_submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'This is an on-time submission',
            'submission_date': datetime.now()  # Before deadline
        })
        
        # Verify submission workflow
        self.assertTrue(on_time_submission.id)
        on_time_submission.act_submit()
        self.assertEqual(on_time_submission.state, 'submit')
    
    def test_deadline_edge_cases(self):
        """Test deadline edge cases."""
        
        # Test same date for issue and submission (edge case)
        same_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        
        grading_assignment = self.grading_assignment.create({
            'name': 'Same Date Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': same_date,
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': same_date + timedelta(hours=1)  # Slightly later same day
        })
        
        assignment = self.op_assignment.create(assignment_data)
        self.assertTrue(assignment.id)
    
    def test_deadline_with_timezone_considerations(self):
        """Test deadline handling with different timezones."""
        
        # Create assignment with specific datetime
        issue_datetime = datetime(2024, 1, 15, 9, 0, 0)  # 9 AM
        submission_datetime = datetime(2024, 1, 20, 23, 59, 59)  # 11:59 PM same day
        
        grading_assignment = self.grading_assignment.create({
            'name': 'Timezone Test Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': issue_datetime,
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': submission_datetime
        })
        
        assignment = self.op_assignment.create(assignment_data)
        self.assertTrue(assignment.id)
    
    def test_bulk_deadline_operations(self):
        """Test bulk operations with deadline management."""
        
        # Create multiple assignments with different deadlines
        assignments = []
        base_date = datetime.now()
        
        for i in range(5):
            issue_date = base_date + timedelta(days=i)
            submission_date = base_date + timedelta(days=i+7)
            
            grading_assignment = self.grading_assignment.create({
                'name': f'Bulk Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': issue_date,
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data.update({
                'grading_assignment_id': grading_assignment.id,
                'submission_date': submission_date
            })
            
            assignment = self.op_assignment.create(assignment_data)
            assignments.append(assignment)
        
        # Verify all assignments created successfully
        self.assertEqual(len(assignments), 5)
        
        # Test bulk deadline updates (should respect validation)
        for assignment in assignments:
            # Valid update
            new_deadline = assignment.submission_date + timedelta(days=1)
            assignment.write({'submission_date': new_deadline})
            self.assertEqual(assignment.submission_date, new_deadline)
    
    def test_deadline_notification_requirements(self):
        """Test deadline-related data for notification systems."""
        
        # Create assignment approaching deadline
        soon_deadline = datetime.now() + timedelta(days=1)
        
        grading_assignment = self.grading_assignment.create({
            'name': 'Approaching Deadline Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now() - timedelta(days=5),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': soon_deadline
        })
        
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Test data needed for notifications
        time_until_deadline = assignment.submission_date - datetime.now()
        self.assertLess(time_until_deadline.days, 2)
        
        # Verify assignment has required data for notifications
        self.assertTrue(assignment.allocation_ids)  # Students to notify
        self.assertTrue(assignment.submission_date)  # Deadline
        self.assertTrue(assignment.name)  # Assignment name
        self.assertEqual(assignment.state, 'publish')  # Must be published
    
    def test_deadline_extension_scenarios(self):
        """Test deadline extension scenarios."""
        
        # Create assignment
        original_deadline = datetime.now() + timedelta(days=3)
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': original_deadline
        })
        
        assignment = self.op_assignment.create(assignment_data)
        
        # Extend deadline
        extended_deadline = original_deadline + timedelta(days=2)
        assignment.write({'submission_date': extended_deadline})
        
        self.assertEqual(assignment.submission_date, extended_deadline)
    
    def test_deadline_with_submission_workflow(self):
        """Test deadline interactions with submission workflow."""
        
        # Create assignment with tight deadline
        tight_deadline = datetime.now() + timedelta(hours=2)
        grading_assignment = self.grading_assignment.create({
            'name': 'Tight Deadline Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now() - timedelta(hours=1),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': tight_deadline
        })
        
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission before deadline
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Rush submission',
            'submission_date': datetime.now()
        })
        
        # Test submission workflow still works normally
        submission.act_submit()
        self.assertEqual(submission.state, 'submit')
        
        submission.act_accept()
        self.assertEqual(submission.state, 'accept')
    
    def test_date_field_constraints_comprehensive(self):
        """Comprehensive test of date field constraints."""
        
        # Test with None values
        grading_assignment_none = self.grading_assignment.create({
            'name': 'None Date Test',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': None,  # None value
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment_none.id,
            'submission_date': None  # None value
        })
        
        # Should not raise validation error with None values
        assignment_none = self.op_assignment.create(assignment_data)
        self.assertTrue(assignment_none.id)
        
        # Test constraint only applies when both dates are present
        assignment_none.write({
            'issued_date': datetime.now(),
            'submission_date': datetime.now() + timedelta(days=1)
        })
        
        # Should work fine
        self.assertTrue(assignment_none.submission_date)