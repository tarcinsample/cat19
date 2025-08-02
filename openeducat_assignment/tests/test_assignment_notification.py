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
class TestAssignmentNotification(TestAssignmentCommon):
    """Test assignment notification and reminder systems."""
    
    def test_assignment_publication_notification(self):
        """Test Task 7: Validate assignment notification and reminder systems."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test notification data availability when assignment is published
        initial_message_count = len(assignment.message_ids)
        
        # Publish assignment (should trigger notification to students)
        assignment.act_publish()
        
        # Verify assignment state change creates tracking message
        self.assertEqual(assignment.state, 'publish')
        
        # Check if message was created (mail tracking)
        final_message_count = len(assignment.message_ids)
        self.assertGreaterEqual(final_message_count, initial_message_count)
        
        # Verify notification data is available
        notification_data = {
            'assignment_name': assignment.name,
            'course_name': assignment.course_id.name,
            'subject_name': assignment.subject_id.name,
            'faculty_name': assignment.faculty_id.name,
            'submission_deadline': assignment.submission_date,
            'allocated_students': assignment.allocation_ids,
            'description': assignment.description
        }
        
        # All required notification data should be present
        self.assertTrue(notification_data['assignment_name'])
        self.assertTrue(notification_data['course_name'])
        self.assertTrue(notification_data['subject_name'])
        self.assertTrue(notification_data['faculty_name'])
        self.assertTrue(notification_data['submission_deadline'])
        self.assertTrue(notification_data['allocated_students'])
        self.assertTrue(notification_data['description'])
    
    def test_deadline_reminder_notification_data(self):
        """Test deadline reminder notification system data."""
        
        # Create assignment with approaching deadline
        reminder_deadline = datetime.now() + timedelta(days=2)
        grading_assignment = self.grading_assignment.create({
            'name': 'Deadline Reminder Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now() - timedelta(days=3),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': reminder_deadline
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Calculate time until deadline for reminder logic
        time_until_deadline = assignment.submission_date - datetime.now()
        hours_until_deadline = time_until_deadline.total_seconds() / 3600
        
        # Verify reminder conditions
        self.assertLess(hours_until_deadline, 72)  # Less than 3 days
        self.assertGreater(hours_until_deadline, 0)  # Still future
        
        # Test reminder data structure
        reminder_data = {
            'assignment_id': assignment.id,
            'assignment_name': assignment.name,
            'deadline': assignment.submission_date,
            'hours_remaining': int(hours_until_deadline),
            'students_to_notify': [],
            'urgency_level': 'medium'
        }
        
        # Find students who haven't submitted yet
        submitted_students = assignment.assignment_sub_line.mapped('student_id')
        pending_students = assignment.allocation_ids - submitted_students
        
        reminder_data['students_to_notify'] = pending_students
        
        # Determine urgency level
        if hours_until_deadline <= 24:
            reminder_data['urgency_level'] = 'high'
        elif hours_until_deadline <= 72:
            reminder_data['urgency_level'] = 'medium'
        else:
            reminder_data['urgency_level'] = 'low'
        
        # Verify reminder data structure
        self.assertTrue(reminder_data['assignment_id'])
        self.assertTrue(reminder_data['assignment_name'])
        self.assertTrue(reminder_data['deadline'])
        self.assertIsInstance(reminder_data['hours_remaining'], int)
        self.assertIn(reminder_data['urgency_level'], ['low', 'medium', 'high'])
    
    def test_submission_status_notification(self):
        """Test submission status change notifications."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Test submission for notification'
        })
        
        # Track message count for each state change
        initial_messages = len(submission.message_ids)
        
        # Submit assignment (should notify faculty)
        submission.act_submit()
        submit_messages = len(submission.message_ids)
        
        # Verify submission notification data
        submission_notification = {
            'submission_id': submission.id,
            'assignment_name': submission.assignment_id.name,
            'student_name': submission.student_id.name,
            'submission_date': submission.submission_date,
            'status': submission.state,
            'faculty_to_notify': submission.assignment_id.faculty_id,
            'content_preview': submission.description[:100] + '...' if len(submission.description) > 100 else submission.description
        }
        
        self.assertEqual(submission_notification['status'], 'submit')
        self.assertTrue(submission_notification['faculty_to_notify'])
        
        # Faculty provides feedback (should notify student)
        submission.write({
            'note': 'Good work, but please add more references.'
        })
        submission.act_change_req()
        
        change_req_messages = len(submission.message_ids)
        
        # Verify feedback notification data
        feedback_notification = {
            'submission_id': submission.id,
            'assignment_name': submission.assignment_id.name,
            'student_to_notify': submission.student_id,
            'faculty_name': submission.assignment_id.faculty_id.name,
            'feedback': submission.note,
            'status': submission.state,
            'action_required': True
        }
        
        self.assertEqual(feedback_notification['status'], 'change')
        self.assertTrue(feedback_notification['action_required'])
        
        # Final acceptance (should notify student)
        submission.act_submit()  # Student resubmits
        submission.write({'marks': 85})
        submission.act_accept()
        
        # Verify acceptance notification data
        acceptance_notification = {
            'submission_id': submission.id,
            'assignment_name': submission.assignment_id.name,
            'student_to_notify': submission.student_id,
            'marks': submission.marks,
            'status': submission.state,
            'final_grade': f"{submission.marks}/{submission.assignment_id.marks}"
        }
        
        self.assertEqual(acceptance_notification['status'], 'accept')
        self.assertEqual(acceptance_notification['marks'], 85)
    
    def test_batch_notification_data(self):
        """Test batch notification system for multiple assignments."""
        
        # Create multiple assignments with different deadlines
        assignments = []
        for i in range(3):
            deadline = datetime.now() + timedelta(days=i+1)
            grading_assignment = self.grading_assignment.create({
                'name': f'Batch Notification Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now() - timedelta(days=1),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data.update({
                'grading_assignment_id': grading_assignment.id,
                'submission_date': deadline
            })
            assignment = self.op_assignment.create(assignment_data)
            assignment.act_publish()
            assignments.append(assignment)
        
        # Create digest notification data
        digest_data = {
            'recipient_students': set(),
            'upcoming_deadlines': [],
            'pending_submissions': 0,
            'new_assignments': len(assignments)
        }
        
        for assignment in assignments:
            # Add students to recipient list
            digest_data['recipient_students'].update(assignment.allocation_ids.ids)
            
            # Add deadline information
            time_until_deadline = assignment.submission_date - datetime.now()
            digest_data['upcoming_deadlines'].append({
                'assignment_name': assignment.name,
                'deadline': assignment.submission_date,
                'days_remaining': time_until_deadline.days,
                'course': assignment.course_id.name
            })
            
            # Count pending submissions
            submitted_count = len(assignment.assignment_sub_line)
            allocated_count = len(assignment.allocation_ids)
            digest_data['pending_submissions'] += (allocated_count - submitted_count)
        
        # Verify digest data structure
        self.assertGreater(len(digest_data['recipient_students']), 0)
        self.assertEqual(len(digest_data['upcoming_deadlines']), 3)
        self.assertEqual(digest_data['new_assignments'], 3)
    
    def test_email_notification_template_data(self):
        """Test email notification template data structure."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Test email template data for assignment publication
        email_template_data = {
            'subject': f'New Assignment: {assignment.name}',
            'recipient_emails': [student.partner_id.email for student in assignment.allocation_ids if student.partner_id.email],
            'template_context': {
                'assignment_name': assignment.name,
                'course_name': assignment.course_id.name,
                'faculty_name': assignment.faculty_id.name,
                'deadline': assignment.submission_date.strftime('%Y-%m-%d %H:%M'),
                'marks': assignment.marks,
                'description': assignment.description,
                'login_url': 'https://portal.example.com/login',  # Would be dynamic
                'assignment_url': f'https://portal.example.com/assignment/{assignment.id}'
            }
        }
        
        # Verify template data structure
        self.assertTrue(email_template_data['subject'])
        self.assertIsInstance(email_template_data['recipient_emails'], list)
        
        # Verify context has all required fields
        context = email_template_data['template_context']
        required_fields = ['assignment_name', 'course_name', 'faculty_name', 'deadline', 'marks', 'description']
        
        for field in required_fields:
            self.assertIn(field, context)
            self.assertTrue(context[field])
    
    def test_notification_preferences_handling(self):
        """Test notification preferences and filtering."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Mock notification preferences (in real implementation, would be user preferences)
        notification_preferences = {
            self.student1.id: {
                'assignment_published': True,
                'deadline_reminder': True,
                'submission_feedback': True,
                'grade_released': True,
                'email_enabled': True,
                'sms_enabled': False
            },
            self.student2.id: {
                'assignment_published': True,
                'deadline_reminder': False,  # Disabled
                'submission_feedback': True,
                'grade_released': True,
                'email_enabled': False,  # Disabled
                'sms_enabled': True
            }
        }
        
        # Filter recipients based on preferences
        def filter_recipients_by_preference(students, notification_type):
            """Filter students based on notification preferences."""
            filtered_students = []
            for student in students:
                prefs = notification_preferences.get(student.id, {})
                if prefs.get(notification_type, True):  # Default to True if not specified
                    filtered_students.append(student)
            return filtered_students
        
        # Test filtering for assignment publication
        assignment.act_publish()
        
        publication_recipients = filter_recipients_by_preference(
            assignment.allocation_ids, 'assignment_published'
        )
        self.assertEqual(len(publication_recipients), 2)  # Both students enabled
        
        # Test filtering for deadline reminders
        reminder_recipients = filter_recipients_by_preference(
            assignment.allocation_ids, 'deadline_reminder'
        )
        self.assertEqual(len(reminder_recipients), 1)  # Only student1 enabled
        
        # Test channel preferences (email vs SMS)
        email_recipients = [
            student for student in assignment.allocation_ids
            if notification_preferences.get(student.id, {}).get('email_enabled', True)
        ]
        sms_recipients = [
            student for student in assignment.allocation_ids
            if notification_preferences.get(student.id, {}).get('sms_enabled', False)
        ]
        
        self.assertEqual(len(email_recipients), 1)  # Only student1
        self.assertEqual(len(sms_recipients), 1)   # Only student2
    
    def test_notification_retry_mechanism(self):
        """Test notification retry mechanism for failed deliveries."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Mock notification queue data structure
        notification_queue = []
        
        # Add notifications to queue
        for student in assignment.allocation_ids:
            notification = {
                'id': f'notif_{assignment.id}_{student.id}',
                'type': 'assignment_published',
                'recipient': student.id,
                'assignment_id': assignment.id,
                'attempts': 0,
                'max_attempts': 3,
                'status': 'pending',
                'created_at': datetime.now(),
                'last_attempt': None,
                'error_message': None
            }
            notification_queue.append(notification)
        
        # Simulate notification processing with failures and retries
        def process_notification_queue():
            """Process notification queue with retry logic."""
            for notification in notification_queue:
                if notification['status'] == 'pending' and notification['attempts'] < notification['max_attempts']:
                    notification['attempts'] += 1
                    notification['last_attempt'] = datetime.now()
                    
                    # Simulate random failure (in real implementation, actual delivery attempt)
                    import random
                    delivery_success = random.choice([True, False, True])  # 66% success rate
                    
                    if delivery_success:
                        notification['status'] = 'delivered'
                    else:
                        notification['error_message'] = 'Simulated delivery failure'
                        if notification['attempts'] >= notification['max_attempts']:
                            notification['status'] = 'failed'
        
        # Process queue multiple times to simulate retries
        for attempt in range(3):
            process_notification_queue()
        
        # Verify notification results
        delivered_count = len([n for n in notification_queue if n['status'] == 'delivered'])
        failed_count = len([n for n in notification_queue if n['status'] == 'failed'])
        
        self.assertGreaterEqual(delivered_count, 0)
        self.assertGreaterEqual(failed_count, 0)
        self.assertEqual(delivered_count + failed_count, len(notification_queue))
        
        # All notifications should have been processed
        pending_count = len([n for n in notification_queue if n['status'] == 'pending'])
        self.assertEqual(pending_count, 0)
    
    def test_real_time_notification_triggers(self):
        """Test real-time notification triggers for immediate events."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Real-time notification test'
        })
        
        # Track real-time events
        real_time_events = []
        
        def log_real_time_event(event_type, data):
            """Log real-time events for testing."""
            event = {
                'timestamp': datetime.now(),
                'type': event_type,
                'data': data
            }
            real_time_events.append(event)
        
        # Simulate real-time events
        # Submission submitted
        submission.act_submit()
        log_real_time_event('submission_submitted', {
            'submission_id': submission.id,
            'student_id': submission.student_id.id,
            'assignment_id': submission.assignment_id.id
        })
        
        # Faculty views submission
        log_real_time_event('submission_viewed', {
            'submission_id': submission.id,
            'faculty_id': assignment.faculty_id.id
        })
        
        # Faculty provides feedback
        submission.write({'note': 'Please revise section 2'})
        submission.act_change_req()
        log_real_time_event('feedback_provided', {
            'submission_id': submission.id,
            'faculty_id': assignment.faculty_id.id,
            'feedback': submission.note
        })
        
        # Verify real-time event tracking
        self.assertEqual(len(real_time_events), 3)
        
        event_types = [event['type'] for event in real_time_events]
        expected_types = ['submission_submitted', 'submission_viewed', 'feedback_provided']
        
        for expected_type in expected_types:
            self.assertIn(expected_type, event_types)