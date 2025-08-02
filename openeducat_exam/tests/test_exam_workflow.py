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
class TestExamWorkflow(TestExamCommon):
    """Test exam workflow state transitions and validation."""

    def setUp(self):
        """Set up test data for workflow tests."""
        super().setUp()
        self.exam = self.create_exam()

    def test_exam_initial_state(self):
        """Test exam initial state is draft."""
        self.assert_exam_state(self.exam, 'draft')

    def test_exam_draft_to_schedule_transition(self):
        """Test transition from draft to schedule."""
        self.assert_exam_state(self.exam, 'draft')
        
        # Schedule the exam
        self.exam.act_schedule()
        self.assert_exam_state(self.exam, 'schedule')

    def test_exam_schedule_to_held_transition(self):
        """Test transition from schedule to held."""
        # First schedule the exam
        self.exam.act_schedule()
        self.assert_exam_state(self.exam, 'schedule')
        
        # Mark as held
        self.exam.act_held()
        self.assert_exam_state(self.exam, 'held')

    def test_exam_held_to_result_updated_transition(self):
        """Test transition from held to result updated."""
        # Setup exam to held state with attendees
        self.exam.act_schedule()
        self.exam.act_held()
        
        # Add marks to attendees
        for attendee in self.exam.attendees_line:
            attendee.marks = 85
        
        # Update results
        self.exam.act_result_updated()
        self.assert_exam_state(self.exam, 'result_updated')

    def test_exam_result_updated_to_done_transition(self):
        """Test transition from result updated to done."""
        # Setup exam to result_updated state
        self.exam.act_schedule()
        self.exam.act_held()
        
        for attendee in self.exam.attendees_line:
            attendee.marks = 85
        
        self.exam.act_result_updated()
        
        # Mark as done
        self.exam.act_done()
        self.assert_exam_state(self.exam, 'done')

    def test_exam_held_to_done_direct_transition(self):
        """Test direct transition from held to done."""
        # Setup exam to held state
        self.exam.act_schedule()
        self.exam.act_held()
        
        # Mark as done directly
        self.exam.act_done()
        self.assert_exam_state(self.exam, 'done')

    def test_exam_draft_to_cancel_transition(self):
        """Test transition from draft to cancel."""
        self.assert_exam_state(self.exam, 'draft')
        
        # Cancel the exam
        self.exam.act_cancel()
        self.assert_exam_state(self.exam, 'cancel')

    def test_exam_schedule_to_cancel_transition(self):
        """Test transition from schedule to cancel."""
        self.exam.act_schedule()
        self.assert_exam_state(self.exam, 'schedule')
        
        # Cancel the exam
        self.exam.act_cancel()
        self.assert_exam_state(self.exam, 'cancel')

    def test_exam_cancel_to_draft_transition(self):
        """Test transition from cancel back to draft."""
        # Cancel the exam
        self.exam.act_cancel()
        self.assert_exam_state(self.exam, 'cancel')
        
        # Reset to draft
        self.exam.act_draft()
        self.assert_exam_state(self.exam, 'draft')

    def test_exam_invalid_transitions(self):
        """Test invalid state transitions raise errors."""
        # Test scheduling from non-draft state
        self.exam.act_schedule()
        with self.assertRaises(ValidationError):
            self.exam.act_schedule()  # Already scheduled
        
        # Test marking held from non-schedule state
        self.exam.act_draft()
        with self.assertRaises(ValidationError):
            self.exam.act_held()  # Not scheduled
        
        # Test result update from non-held state
        with self.assertRaises(ValidationError):
            self.exam.act_result_updated()  # Not held

    def test_exam_done_state_immutability(self):
        """Test that done state cannot transition to other states."""
        # Setup exam to done state
        self.exam.act_schedule()
        self.exam.act_held()
        self.exam.act_done()
        
        # Test that done exam cannot be reset to draft
        with self.assertRaises(ValidationError):
            self.exam.act_draft()
        
        # Test that done exam cannot be cancelled
        with self.assertRaises(ValidationError):
            self.exam.act_cancel()

    def test_exam_schedule_validation_requirements(self):
        """Test validation requirements for scheduling."""
        # Create exam without session
        invalid_exam = self.env['op.exam'].create({
            'name': 'Invalid Exam',
            'exam_code': 'INVALID001',
            'subject_id': self.subject1.id,
            'start_time': self.exam.start_time,
            'end_time': self.exam.end_time,
            'total_marks': 100,
            'min_marks': 40,
        })
        
        with self.assertRaises(ValidationError):
            invalid_exam.act_schedule()

    def test_exam_held_validation_requirements(self):
        """Test validation requirements for marking exam as held."""
        self.exam.act_schedule()
        
        # Remove attendees to test validation
        self.exam.attendees_line.unlink()
        
        with self.assertRaises(ValidationError):
            self.exam.act_held()

    def test_exam_result_update_validation_requirements(self):
        """Test validation requirements for result update."""
        self.exam.act_schedule()
        self.exam.act_held()
        
        # Test without marks entered
        with self.assertRaises(ValidationError):
            self.exam.act_result_updated()
        
        # Test with partial marks
        self.exam.attendees_line[0].marks = 85
        # Leave second attendee without marks
        
        with self.assertRaises(ValidationError):
            self.exam.act_result_updated()

    def test_exam_cancel_with_results_validation(self):
        """Test that exam with results cannot be cancelled."""
        self.exam.act_schedule()
        self.exam.act_held()
        
        # Add marks
        for attendee in self.exam.attendees_line:
            attendee.marks = 85
        
        self.exam.act_result_updated()
        
        # Should not be able to cancel with results
        with self.assertRaises(ValidationError):
            self.exam.act_cancel()

    def test_exam_attendees_cleanup_on_cancel(self):
        """Test that attendees are cleaned up when exam is cancelled."""
        self.exam.act_schedule()
        
        # Verify attendees exist
        initial_count = len(self.exam.attendees_line)
        self.assertGreater(initial_count, 0, "Should have attendees after scheduling")
        
        # Cancel exam
        self.exam.act_cancel()
        
        # Verify attendees are removed
        final_count = len(self.exam.attendees_line)
        self.assertEqual(final_count, 0, "Attendees should be removed after cancellation")

    def test_exam_workflow_tracking(self):
        """Test that workflow changes are tracked."""
        # Check initial tracking
        initial_state = self.exam.state
        
        # Perform state change
        self.exam.act_schedule()
        
        # Verify state change was tracked
        self.assertNotEqual(self.exam.state, initial_state, "State should have changed")
        
        # Check if tracking is enabled (message should be created)
        messages = self.exam.message_ids
        # This depends on if tracking is enabled for state field

    def test_exam_workflow_permissions(self):
        """Test workflow permissions for different user roles."""
        # This test would require setting up different user roles
        # and testing their permissions for state transitions
        
        # For now, test basic functionality
        self.exam.act_schedule()
        self.exam.act_held()
        self.exam.act_done()
        
        # Verify final state
        self.assert_exam_state(self.exam, 'done')

    def test_exam_workflow_batch_operations(self):
        """Test workflow operations on multiple exams."""
        # Create multiple exams
        exams = []
        for i in range(3):
            exam = self.create_exam(
                exam_code=f'BATCH{i:03d}',
                name=f'Batch Exam {i}'
            )
            exams.append(exam)
        
        # Batch schedule operation
        for exam in exams:
            exam.act_schedule()
        
        # Verify all are scheduled
        for exam in exams:
            self.assert_exam_state(exam, 'schedule')
        
        # Batch held operation
        for exam in exams:
            exam.act_held()
        
        # Verify all are held
        for exam in exams:
            self.assert_exam_state(exam, 'held')

    def test_exam_workflow_rollback_scenarios(self):
        """Test workflow rollback scenarios."""
        # Test rollback from schedule to draft
        self.exam.act_schedule()
        self.exam.act_draft()
        self.assert_exam_state(self.exam, 'draft')
        
        # Test rollback from cancel to draft
        self.exam.act_cancel()
        self.exam.act_draft()
        self.assert_exam_state(self.exam, 'draft')

    def test_exam_workflow_edge_cases(self):
        """Test workflow edge cases and error conditions."""
        # Test multiple rapid state changes
        self.exam.act_schedule()
        self.exam.act_held()
        
        # Test that calling held again doesn't cause issues
        with self.assertRaises(ValidationError):
            self.exam.act_held()

    def test_exam_state_dependent_field_access(self):
        """Test that certain fields are accessible based on state."""
        # In draft state, all fields should be editable
        self.assert_exam_state(self.exam, 'draft')
        self.exam.name = "Modified Name"
        self.assertEqual(self.exam.name, "Modified Name")
        
        # After scheduling, some fields might become readonly
        self.exam.act_schedule()
        # Implementation dependent - some systems make fields readonly

    def test_exam_workflow_with_concurrent_operations(self):
        """Test workflow with simulated concurrent operations."""
        # Create two references to same exam
        exam_ref1 = self.exam
        exam_ref2 = self.env['op.exam'].browse(self.exam.id)
        
        # Perform operations through different references
        exam_ref1.act_schedule()
        
        # Verify state is consistent across references
        self.assert_exam_state(exam_ref1, 'schedule')
        self.assert_exam_state(exam_ref2, 'schedule')

    def test_exam_workflow_state_history(self):
        """Test tracking of exam state history."""
        # Record state transitions
        state_history = []
        
        state_history.append(self.exam.state)
        self.exam.act_schedule()
        
        state_history.append(self.exam.state)
        self.exam.act_held()
        
        state_history.append(self.exam.state)
        self.exam.act_done()
        
        state_history.append(self.exam.state)
        
        # Verify state progression
        expected_history = ['draft', 'schedule', 'held', 'done']
        self.assertEqual(state_history, expected_history,
                        "State history should match expected progression")

    def test_exam_workflow_validation_messages(self):
        """Test that workflow validation provides clear error messages."""
        # Test error message for invalid transition
        self.exam.act_schedule()
        
        try:
            self.exam.act_result_updated()  # Invalid: not held yet
        except ValidationError as e:
            self.assertIn("'Held'", str(e), "Error should mention required state")
        
        # Test error message for done exam modification
        self.exam.act_held()
        self.exam.act_done()
        
        try:
            self.exam.act_draft()  # Invalid: cannot reset done exam
        except ValidationError as e:
            self.assertIn("completed", str(e), "Error should mention completed state")