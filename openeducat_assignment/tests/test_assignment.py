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
from logging import info

from odoo.exceptions import ValidationError
from .test_assignment_common import TestAssignmentCommon


class TestAssignment(TestAssignmentCommon):

    def setUp(self):
        super(TestAssignment, self).setUp()

    def test_case_assignment(self):
        """Test assignment creation and workflow states."""
        # Create test assignment instead of relying on existing data
        assignment = self.op_assignment.create(self.assignment_data)
        
        info('Details of Assignment')
        info('      Name : %s' % assignment.name)
        info('      Course : %s' % assignment.course_id.id)
        info('      Batch : %s' % assignment.batch_id.id)
        info('      Subject : %s' % assignment.subject_id.id)
        info('      Faculty : %s' % assignment.faculty_id.id)
        info('      Assignment Type : %s' % assignment.assignment_type.id)
        info('      Marks : %s' % assignment.marks)
        info('      Description : %s' % assignment.description)
        info('      State : %s' % assignment.state)
        info('      Issued_date : %s' % assignment.issued_date)
        info('      Submission_date : %s' % assignment.submission_date)
        info('      Allocation Ids : %s' % assignment.allocation_ids.ids)
        info('      Assignments : %s' % assignment.assignment_sub_line)
        info('      Reviewer : %s' % assignment.reviewer.id if assignment.reviewer else 'None')
        
        # Test workflow methods starting from draft state
        self.assertEqual(assignment.state, 'draft')
        
        # Test onchange method
        assignment.onchange_course()
        
        # Test state transitions
        assignment.act_publish()
        self.assertEqual(assignment.state, 'publish')
        
        # Create a submission to test cancel validation
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Test submission for cancel validation',
            'state': 'draft',
            'submission_date': datetime.now()  # Add required submission_date
        })
        
        # Test that we cannot cancel with existing submissions
        with self.assertRaises(ValidationError):
            assignment.act_cancel()
        
        # Remove submission and test cancel
        submission.unlink()
        assignment.act_cancel()
        self.assertEqual(assignment.state, 'cancel')
        
        # Test reset to draft
        assignment.act_set_to_draft()
        self.assertEqual(assignment.state, 'draft')
        
        # Test finish workflow from published state
        assignment.act_publish()
        assignment.act_finish()
        self.assertEqual(assignment.state, 'finish')


class TestAssignmentSubline(TestAssignmentCommon):

    def setUp(self):
        super(TestAssignmentSubline, self).setUp()

    def test_case_assignment_subline(self):
        assignment_subline = self.op_assignment_subline.search([])
        
        # Create assignment using test data
        assignment = self.env["op.assignment"].create(self.assignment_data)
        
        # Override some fields for this specific test
        assignment.write({
            'name': "LRTP - 001 - Asg - 009",
            'marks': 50,
            'description': 'Please answer the following questions briefly: - 1. What are the different types of land'
        })
        assignment_subline1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'state': "draft",
            'student_id': self.student1.id,
            'description': 'The answers of the questions are placed here',
            'submission_date': datetime.now()  # Add required submission_date
        })
        assignment_subline1.unlink()
        for record in assignment_subline:
            info('      Assignment Name : %s' % record.assignment_id.id)
            info('      Student : %s' % record.student_id.id)
            info('      Description : %s' % record.description)
            info('      State : %s' % record.state)
            info('      submission_date : %s' % record.submission_date)
            info('      Marks : %s' % record.marks)
            info('      Note : %s' % record.note)
            info('      User : %s' % record.user_id.id)
            info('      Faculty : %s' % record.faculty_user_id.id)
            info('      Check User Boolean : %s' % record.user_boolean)
            record.act_draft()
            record.act_submit()
            record.act_accept()
            record.act_change_req()
            record.act_reject()
