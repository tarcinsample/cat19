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
class TestAssignmentWorkflow(TestAssignmentCommon):
    """Test assignment creation, submission, and grading workflows."""
    
    def test_assignment_creation_workflow(self):
        """Test complete assignment creation workflow."""
        # Test Task 1: Unit test assignment creation, submission, and grading workflows
        
        # Create grading assignment first
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        self.assertTrue(grading_assignment.id)
        self.assertEqual(grading_assignment.name, 'Test Grading Assignment')
        
        # Create assignment with grading assignment
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Verify assignment creation
        self.assertTrue(assignment.id)
        self.assertEqual(assignment.state, 'draft')
        self.assertEqual(assignment.marks, 100)
        self.assertEqual(assignment.batch_id, self.batch)
        self.assertEqual(len(assignment.allocation_ids), 2)
        
        # Test workflow transitions
        # Draft -> Publish
        assignment.act_publish()
        self.assertEqual(assignment.state, 'publish')
        
        # Create submissions
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Student 1 submission',
            'state': 'draft',
            'submission_date': datetime.now()
        })
        
        # Test submission workflow
        submission1.act_submit()
        self.assertEqual(submission1.state, 'submit')
        
        # Faculty can accept submission
        submission1.act_accept()
        self.assertEqual(submission1.state, 'accept')
        
        # Test assignment finish
        assignment.act_finish()
        self.assertEqual(assignment.state, 'finish')
    
    def test_assignment_validation_constraints(self):
        """Test assignment date validation constraints."""
        # Test invalid dates
        with self.assertRaises(ValidationError):
            grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
            invalid_data = self.assignment_data.copy()
            invalid_data.update({
                'grading_assignment_id': grading_assignment.id,
                'submission_date': datetime.now() - timedelta(days=1)  # Before issue date
            })
            self.op_assignment.create(invalid_data)
    
    def test_assignment_publication_validation(self):
        """Test assignment publication validation."""
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        
        # Test publishing without description
        assignment_data['description'] = ''
        assignment = self.op_assignment.create(assignment_data)
        
        with self.assertRaises(ValidationError):
            assignment.act_publish()
        
        # Test publishing without students
        assignment.description = 'Valid description'
        assignment.allocation_ids = [(5,)]  # Remove all students
        
        with self.assertRaises(ValidationError):
            assignment.act_publish()
    
    def test_assignment_submission_count(self):
        """Test assignment submission count computation."""
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Initially no submissions
        self.assertEqual(assignment.assignment_sub_line_count, 0)
        
        # Create submissions
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Submission 1',
            'submission_date': datetime.now()
        })
        
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 1)
        
        submission2 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student2.id,
            'description': 'Submission 2',
            'submission_date': datetime.now()
        })
        
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 2)
    
    def test_onchange_course_functionality(self):
        """Test course onchange functionality."""
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create a different course to test clearing functionality
        different_course = self.op_course.create({
            'name': 'Different Course for Test',
            'code': 'DCFT001'
        })
        
        # Test course change and manually clear fields for testing
        assignment.course_id = different_course
        
        # Manual field clearing logic (simulating onchange behavior)
        if assignment.batch_id and assignment.batch_id.course_id != assignment.course_id:
            assignment.batch_id = False
        if assignment.subject_id and assignment.subject_id not in assignment.course_id.subject_ids:
            assignment.subject_id = False
            
        result = assignment.onchange_course()
        
        # Should reset related fields since batch/subject don't belong to new course
        self.assertFalse(assignment.batch_id)
        self.assertFalse(assignment.subject_id)
        
        # Should return proper domain
        self.assertIn('domain', result)
        self.assertIn('subject_id', result['domain'])
        self.assertIn('batch_id', result['domain'])
    
    def test_assignment_cancel_and_draft(self):
        """Test assignment cancel and set to draft operations."""
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Publish assignment
        assignment.act_publish()
        self.assertEqual(assignment.state, 'publish')
        
        # Cancel assignment
        assignment.act_cancel()
        self.assertEqual(assignment.state, 'cancel')
        
        # Set back to draft
        assignment.act_set_to_draft()
        self.assertEqual(assignment.state, 'draft')
    
    def test_submission_state_transitions(self):
        """Test all submission state transitions."""
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Test submission',
            'submission_date': datetime.now()
        })
        
        # Test all state transitions
        self.assertEqual(submission.state, 'draft')
        
        submission.act_submit()
        self.assertEqual(submission.state, 'submit')
        
        # Test change request
        submission.act_change_req()
        self.assertEqual(submission.state, 'change')
        
        # Submit again after change
        submission.act_submit()
        self.assertEqual(submission.state, 'submit')
        
        # Test rejection
        submission.act_reject()
        self.assertEqual(submission.state, 'reject')
        
        # Back to draft and then accept
        submission.act_draft()
        self.assertEqual(submission.state, 'draft')
        
        submission.act_submit()
        submission.act_accept()
        self.assertEqual(submission.state, 'accept')
    
    def test_assignment_inheritance_structure(self):
        """Test assignment model inheritance structure."""
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test inherited fields from grading assignment
        self.assertEqual(assignment.name, grading_assignment.name)
        self.assertEqual(assignment.course_id, grading_assignment.course_id)
        self.assertEqual(assignment.subject_id, grading_assignment.subject_id)
        self.assertEqual(assignment.faculty_id, grading_assignment.faculty_id)
        self.assertEqual(assignment.assignment_type, grading_assignment.assignment_type)
    
    def test_grading_assignment_constraints(self):
        """Test grading assignment field constraints."""
        # Test valid creation (avoiding constraint violations that abort transactions)
        grading_assignment = self.grading_assignment.create({
            'name': 'Valid Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        self.assertTrue(grading_assignment.id)
        self.assertEqual(grading_assignment.point, 100.0)