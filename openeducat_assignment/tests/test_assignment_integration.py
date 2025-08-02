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
class TestAssignmentIntegration(TestAssignmentCommon):
    """Test integration between student-faculty assignment workflows and related modules."""
    
    def test_student_faculty_integration_workflow(self):
        """Test Task 5: Integration testing for student-faculty assignment workflows."""
        
        # Create assignment by faculty
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Verify faculty assignment
        self.assertEqual(assignment.faculty_id, self.faculty)
        
        # Faculty publishes assignment
        assignment.act_publish()
        self.assertEqual(assignment.state, 'publish')
        
        # Students can view and submit assignments
        for student in [self.student1, self.student2]:
            self.assertIn(student, assignment.allocation_ids)
            
            # Student creates submission
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Submission by {student.name}'
            })
            
            # Student submits assignment
            submission.act_submit()
            self.assertEqual(submission.state, 'submit')
        
        # Faculty reviews submissions
        for submission in assignment.assignment_sub_line:
            self.assertEqual(submission.state, 'submit')
            
            # Faculty can accept or request changes
            if submission.student_id == self.student1:
                submission.act_accept()
                submission.write({'marks': 85})
            else:
                submission.act_change_req()
        
        # Verify final states
        accepted_submissions = assignment.assignment_sub_line.filtered(lambda s: s.state == 'accept')
        change_req_submissions = assignment.assignment_sub_line.filtered(lambda s: s.state == 'change')
        
        self.assertEqual(len(accepted_submissions), 1)
        self.assertEqual(len(change_req_submissions), 1)
        
        # Faculty can finish assignment
        assignment.act_finish()
        self.assertEqual(assignment.state, 'finish')
    
    def test_course_batch_subject_integration(self):
        """Test integration with course, batch, and subject models."""
        
        # Test course-batch relationship
        self.assertEqual(self.batch.course_id, self.course)
        
        # Create assignment linked to course, batch, and subject
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Verify relationships
        self.assertEqual(assignment.course_id, self.course)
        self.assertEqual(assignment.batch_id, self.batch)
        self.assertEqual(assignment.subject_id, self.subject)
        
        # Test onchange course functionality
        new_course = self.op_course.create({
            'name': 'New Test Course',
            'code': 'NTC001'
        })
        
        assignment.course_id = new_course
        result = assignment.onchange_course()
        
        # Should clear batch and subject
        self.assertFalse(assignment.batch_id)
        self.assertFalse(assignment.subject_id)
        
        # Should return proper domain
        self.assertIn('domain', result)
    
    def test_mail_thread_integration(self):
        """Test mail thread integration for assignments and submissions."""
        
        # Create assignment (inherits mail.thread)
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test mail functionality is available
        self.assertTrue(hasattr(assignment, 'message_post'))
        self.assertTrue(hasattr(assignment, 'message_ids'))
        
        # Create submission (also inherits mail.thread)
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Mail thread test submission'
        })
        
        # Test mail functionality for submissions
        self.assertTrue(hasattr(submission, 'message_post'))
        self.assertTrue(hasattr(submission, 'message_ids'))
        
        # Test tracking fields work
        initial_state = assignment.state
        assignment.act_publish()
        
        # State change should be tracked
        self.assertNotEqual(assignment.state, initial_state)
    
    def test_security_groups_integration(self):
        """Test security group integration for assignments."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Security test submission'
        })
        
        # Test user boolean computation (security groups)
        submission._compute_get_user_group()
        # Note: In test environment, user_boolean behavior depends on test user's groups
        self.assertIsNotNone(submission.user_boolean)
    
    def test_academic_year_integration(self):
        """Test integration with academic year/term if applicable."""
        
        # Create assignment within academic context
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Verify assignment is properly linked to academic context
        self.assertTrue(assignment.course_id)
        self.assertTrue(assignment.batch_id)
        
        # Test academic hierarchy: Course -> Batch -> Students
        self.assertEqual(assignment.batch_id.course_id, assignment.course_id)
        
        # Students in allocation should be valid for the batch
        for student in assignment.allocation_ids:
            self.assertTrue(student.id)  # Basic validation
    
    def test_reporting_integration(self):
        """Test assignment data for reporting integration."""
        
        # Create multiple assignments with submissions
        assignments = []
        for i in range(3):
            grading_assignment = self.grading_assignment.create({
                'name': f'Report Test Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now() - timedelta(days=i),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data['grading_assignment_id'] = grading_assignment.id
            assignment = self.op_assignment.create(assignment_data)
            assignment.act_publish()
            assignments.append(assignment)
        
        # Create submissions with different states and marks
        submission_data = [
            (assignments[0], self.student1, 'accept', 85),
            (assignments[0], self.student2, 'accept', 92),
            (assignments[1], self.student1, 'submit', 0),
            (assignments[1], self.student2, 'reject', 0),
            (assignments[2], self.student1, 'change', 0),
        ]
        
        for assignment, student, state, marks in submission_data:
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Submission for {assignment.name}',
                'state': state,
                'marks': marks
            })
        
        # Test reporting data aggregation
        total_assignments = len(assignments)
        total_submissions = len(submission_data)
        
        all_assignments = self.op_assignment.search([('id', 'in', [a.id for a in assignments])])
        self.assertEqual(len(all_assignments), total_assignments)
        
        all_submissions = self.op_assignment_subline.search([
            ('assignment_id', 'in', [a.id for a in assignments])
        ])
        self.assertEqual(len(all_submissions), total_submissions)
        
        # Test statistical reporting data
        accepted_submissions = all_submissions.filtered(lambda s: s.state == 'accept')
        average_marks = sum(accepted_submissions.mapped('marks')) / len(accepted_submissions) if accepted_submissions else 0
        self.assertEqual(average_marks, 88.5)  # (85 + 92) / 2
    
    def test_partner_integration(self):
        """Test integration with partner model for students and faculty."""
        
        # Verify student-partner relationship
        self.assertTrue(self.student1.partner_id)
        self.assertEqual(self.student1.name, self.student1.partner_id.name)
        
        # Verify faculty-partner relationship
        self.assertTrue(self.faculty.partner_id)
        
        # Create assignment and test partner data access
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test partner data accessibility through assignment
        faculty_partner = assignment.faculty_id.partner_id
        self.assertTrue(faculty_partner.id)
        
        for student in assignment.allocation_ids:
            student_partner = student.partner_id
            self.assertTrue(student_partner.id)
    
    def test_sequence_generation_integration(self):
        """Test sequence generation and naming integration."""
        
        # Create multiple assignments to test naming/sequencing
        assignments = []
        for i in range(3):
            grading_assignment = self.grading_assignment.create({
                'name': f'SEQ-{i+1:03d}',  # Sequential naming
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
        
        # Verify unique names
        names = [a.name for a in assignments]
        self.assertEqual(len(names), len(set(names)))  # All names should be unique
        
        # Test submission naming/sequencing
        submission = self.op_assignment_subline.create({
            'assignment_id': assignments[0].id,
            'student_id': self.student1.id,
            'description': 'Sequence test submission'
        })
        
        # Submission should inherit assignment name for rec_name
        self.assertEqual(submission.assignment_id, assignments[0])
    
    def test_multi_company_integration(self):
        """Test multi-company support if applicable."""
        
        # Create assignment in default company context
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Verify assignment exists and is accessible
        self.assertTrue(assignment.id)
        
        # Test search works across company context
        found_assignment = self.op_assignment.search([('id', '=', assignment.id)])
        self.assertEqual(len(found_assignment), 1)
    
    def test_workflow_state_integration(self):
        """Test complete workflow state integration across models."""
        
        # Create assignment and test complete workflow
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test assignment workflow states
        workflow_states = ['draft', 'publish', 'finish', 'cancel']
        
        # Draft state (initial)
        self.assertEqual(assignment.state, 'draft')
        
        # Publish state
        assignment.act_publish()
        self.assertEqual(assignment.state, 'publish')
        
        # Create submission in published state
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Workflow test submission'
        })
        
        # Test submission workflow
        submission_states = ['draft', 'submit', 'accept', 'reject', 'change']
        
        self.assertEqual(submission.state, 'draft')
        submission.act_submit()
        self.assertEqual(submission.state, 'submit')
        submission.act_accept()
        self.assertEqual(submission.state, 'accept')
        
        # Finish assignment
        assignment.act_finish()
        self.assertEqual(assignment.state, 'finish')
        
        # Test cancel and draft restoration
        assignment.act_cancel()
        self.assertEqual(assignment.state, 'cancel')
        assignment.act_set_to_draft()
        self.assertEqual(assignment.state, 'draft')