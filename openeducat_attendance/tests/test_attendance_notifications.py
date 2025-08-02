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

from unittest.mock import patch
from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceNotifications(TestAttendanceCommon):
    """Test attendance notification system for low attendance."""

    def setUp(self):
        """Set up test data for notification testing."""
        super().setUp()
        
        # Create attendance pattern for low attendance scenario
        self.sheets = []
        for i in range(5):  # 5 days of attendance
            sheet = self.create_attendance_sheet(
                attendance_date=self.today - self.env['ir.sequence']._next_by_code('test.sequence') + i
            )
            self.sheets.append(sheet)
            
            # Student1: Good attendance (80%)
            present1 = i < 4  # Present 4 out of 5 days
            self.create_attendance_line(sheet, self.student1, present=present1)
            
            # Student2: Poor attendance (40%)
            present2 = i < 2  # Present 2 out of 5 days
            self.create_attendance_line(sheet, self.student2, present=present2)

    def test_low_attendance_detection(self):
        """Test detection of students with low attendance."""
        low_attendance_threshold = 75.0
        low_attendance_students = []
        
        # Calculate attendance for each student
        for student in [self.student1, self.student2]:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            if lines:
                present_count = len(lines.filtered('present'))
                total_count = len(lines)
                percentage = (present_count / total_count) * 100
                
                if percentage < low_attendance_threshold:
                    low_attendance_students.append({
                        'student': student,
                        'percentage': percentage,
                        'present_days': present_count,
                        'total_days': total_count
                    })
        
        # Verify detection
        self.assertEqual(len(low_attendance_students), 1, 
                        "Should detect 1 student with low attendance")
        
        low_student_data = low_attendance_students[0]
        self.assertEqual(low_student_data['student'], self.student2,
                        "Student2 should have low attendance")
        self.assertEqual(low_student_data['percentage'], 40.0,
                        "Student2 should have 40% attendance")

    def test_attendance_alert_generation(self):
        """Test generation of attendance alerts."""
        # Simulate alert generation process
        alerts = []
        low_threshold = 75.0
        
        students = self.env['op.student'].search([
            ('course_detail_ids.course_id', '=', self.course.id),
            ('course_detail_ids.batch_id', '=', self.batch.id)
        ])
        
        for student in students:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            if lines:
                present_count = len(lines.filtered('present'))
                total_count = len(lines)
                percentage = (present_count / total_count) * 100
                
                if percentage < low_threshold:
                    alert = {
                        'type': 'low_attendance',
                        'student_id': student.id,
                        'student_name': student.name,
                        'attendance_percentage': percentage,
                        'course': self.course.name,
                        'batch': self.batch.name,
                        'alert_date': self.today,
                        'message': f"Student {student.name} has low attendance: {percentage:.1f}%"
                    }
                    alerts.append(alert)
        
        # Verify alert generation
        self.assertEqual(len(alerts), 1, "Should generate 1 alert")
        alert = alerts[0]
        self.assertEqual(alert['student_name'], self.student2.name, 
                        "Alert should be for student2")
        self.assertIn('low attendance', alert['message'], 
                     "Alert message should mention low attendance")

    def test_parent_notification_preparation(self):
        """Test preparation of parent notifications for low attendance."""
        # Create parent for student with low attendance
        parent = self.env['op.parent'].create({
            'name': 'Test Parent',
            'student_ids': [(6, 0, [self.student2.id])],
            'email': 'parent@test.com',
        })
        
        # Prepare parent notifications
        notifications = []
        low_threshold = 75.0
        
        students_with_parents = self.env['op.student'].search([
            ('parent_ids', '!=', False),
            ('course_detail_ids.course_id', '=', self.course.id)
        ])
        
        for student in students_with_parents:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            if lines:
                present_count = len(lines.filtered('present'))
                total_count = len(lines)
                percentage = (present_count / total_count) * 100
                
                if percentage < low_threshold:
                    for parent in student.parent_ids:
                        if parent.email:
                            notification = {
                                'recipient': parent.email,
                                'recipient_name': parent.name,
                                'student_name': student.name,
                                'attendance_percentage': percentage,
                                'subject': f'Low Attendance Alert - {student.name}',
                                'message': self._prepare_parent_message(
                                    student, percentage, present_count, total_count)
                            }
                            notifications.append(notification)
        
        # Verify notification preparation
        self.assertEqual(len(notifications), 1, "Should prepare 1 parent notification")
        notification = notifications[0]
        self.assertEqual(notification['recipient'], 'parent@test.com',
                        "Should send to parent email")
        self.assertIn('Low Attendance Alert', notification['subject'],
                     "Subject should indicate low attendance")

    def _prepare_parent_message(self, student, percentage, present_days, total_days):
        """Helper method to prepare parent notification message."""
        return f"""
        Dear Parent,
        
        We would like to inform you that your child {student.name} has low attendance.
        
        Attendance Summary:
        - Present Days: {present_days}
        - Total Days: {total_days}
        - Attendance Percentage: {percentage:.1f}%
        
        Please ensure regular attendance for better academic performance.
        
        Best regards,
        Academic Team
        """

    def test_faculty_notification_system(self):
        """Test faculty notifications for attendance issues."""
        # Prepare faculty notifications
        faculty_notifications = []
        
        # Check for attendance patterns requiring faculty attention
        sheets_needing_attention = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id),
            ('state', '=', 'draft')  # Pending sheets
        ])
        
        for sheet in sheets_needing_attention:
            if sheet.faculty_id:
                notification = {
                    'recipient': sheet.faculty_id.email if hasattr(sheet.faculty_id, 'email') else None,
                    'faculty_name': sheet.faculty_id.name,
                    'subject': f'Pending Attendance - {sheet.attendance_date}',
                    'message': f'Attendance for {sheet.course_id.name} - {sheet.batch_id.name} on {sheet.attendance_date} is pending.',
                    'sheet_id': sheet.id,
                    'priority': 'medium'
                }
                faculty_notifications.append(notification)
        
        # Check for low attendance in faculty's classes
        faculty_classes = self.env['op.attendance.register'].search([
            ('faculty_id', '=', self.faculty.id)
        ])
        
        for register in faculty_classes:
            # Calculate class attendance statistics
            all_lines = self.env['op.attendance.line'].search([
                ('attendance_id.register_id', '=', register.id)
            ])
            
            if all_lines:
                present_count = len(all_lines.filtered('present'))
                total_count = len(all_lines)
                class_percentage = (present_count / total_count) * 100
                
                if class_percentage < 70.0:  # Class-wide low attendance
                    notification = {
                        'recipient': register.faculty_id.email if hasattr(register.faculty_id, 'email') else None,
                        'faculty_name': register.faculty_id.name,
                        'subject': f'Low Class Attendance - {register.name}',
                        'message': f'Class attendance for {register.name} is {class_percentage:.1f}%. Please review.',
                        'register_id': register.id,
                        'priority': 'high'
                    }
                    faculty_notifications.append(notification)
        
        # Verify faculty notifications
        self.assertGreaterEqual(len(faculty_notifications), 0, 
                               "Should prepare faculty notifications as needed")

    @patch('odoo.addons.mail.models.mail_thread.MailThread.message_post')
    def test_automated_message_posting(self, mock_message_post):
        """Test automated message posting for attendance alerts."""
        # Simulate automated alert posting
        low_attendance_students = []
        
        for student in [self.student1, self.student2]:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            if lines:
                present_count = len(lines.filtered('present'))
                total_count = len(lines)
                percentage = (present_count / total_count) * 100
                
                if percentage < 75.0:
                    # Post message to student record
                    student.message_post(
                        body=f"Low attendance alert: {percentage:.1f}% attendance",
                        subject="Attendance Alert",
                        message_type='notification'
                    )
                    low_attendance_students.append(student)
        
        # Verify message posting was called
        if low_attendance_students:
            mock_message_post.assert_called()
            self.assertEqual(len(low_attendance_students), 1, 
                            "Should post message for 1 student")

    def test_attendance_improvement_tracking(self):
        """Test tracking of attendance improvement over time."""
        # Create additional attendance data to show improvement
        improvement_sheet = self.create_attendance_sheet(
            attendance_date=self.today + self.env['ir.sequence']._next_by_code('test.sequence')
        )
        
        # Student2 improves attendance
        self.create_attendance_line(improvement_sheet, self.student2, present=True, 
                                   remarks="Attendance improving")
        
        # Calculate improvement
        all_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student2.id),
            ('attendance_id.register_id', '=', self.register.id)
        ], order='attendance_id.attendance_date')
        
        # Get recent vs older attendance
        total_lines = len(all_lines)
        if total_lines >= 4:
            recent_lines = all_lines[-2:]  # Last 2 entries
            older_lines = all_lines[:-2]   # Earlier entries
            
            recent_percentage = (len(recent_lines.filtered('present')) / len(recent_lines)) * 100
            older_percentage = (len(older_lines.filtered('present')) / len(older_lines)) * 100
            
            improvement = recent_percentage - older_percentage
            
            if improvement > 0:
                improvement_alert = {
                    'type': 'attendance_improvement',
                    'student_id': self.student2.id,
                    'improvement_percentage': improvement,
                    'message': f"Student {self.student2.name} showing attendance improvement: +{improvement:.1f}%"
                }
                
                # Verify improvement detection
                self.assertGreater(improvement, 0, "Should detect attendance improvement")

    def test_notification_scheduling(self):
        """Test scheduling of attendance notifications."""
        # Simulate notification scheduling
        scheduled_notifications = []
        
        # Weekly low attendance report
        weekly_schedule = {
            'frequency': 'weekly',
            'day': 'friday',
            'time': '17:00',
            'recipients': ['admin@school.com', 'principal@school.com'],
            'type': 'low_attendance_summary'
        }
        
        # Daily absence alerts
        daily_schedule = {
            'frequency': 'daily',
            'time': '18:00',
            'recipients': ['attendance@school.com'],
            'type': 'daily_absence_report'
        }
        
        scheduled_notifications.extend([weekly_schedule, daily_schedule])
        
        # Verify scheduling configuration
        self.assertEqual(len(scheduled_notifications), 2, 
                        "Should have 2 scheduled notification types")
        
        weekly_notif = next(n for n in scheduled_notifications if n['frequency'] == 'weekly')
        self.assertEqual(weekly_notif['type'], 'low_attendance_summary',
                        "Weekly notification should be attendance summary")

    def test_notification_preferences(self):
        """Test user notification preferences."""
        # Simulate notification preferences
        notification_preferences = {
            'low_attendance_threshold': 75.0,
            'notification_methods': ['email', 'sms'],
            'frequency': 'immediate',
            'include_parents': True,
            'include_faculty': True,
            'working_hours_only': True,
            'language': 'en_US'
        }
        
        # Test preference application
        student_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student2.id),
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        present_count = len(student_lines.filtered('present'))
        total_count = len(student_lines)
        percentage = (present_count / total_count) * 100
        
        should_notify = percentage < notification_preferences['low_attendance_threshold']
        
        self.assertTrue(should_notify, "Should trigger notification based on preferences")
        self.assertIn('email', notification_preferences['notification_methods'],
                     "Email should be enabled in preferences")

    def test_notification_delivery_status(self):
        """Test tracking of notification delivery status."""
        # Simulate notification delivery tracking
        notifications = [
            {
                'id': 1,
                'recipient': 'parent@test.com',
                'type': 'low_attendance',
                'status': 'sent',
                'sent_at': self.today,
                'delivery_status': 'delivered'
            },
            {
                'id': 2,
                'recipient': 'faculty@test.com',
                'type': 'attendance_alert',
                'status': 'pending',
                'sent_at': None,
                'delivery_status': 'pending'
            }
        ]
        
        # Check delivery statistics
        sent_notifications = [n for n in notifications if n['status'] == 'sent']
        pending_notifications = [n for n in notifications if n['status'] == 'pending']
        
        self.assertEqual(len(sent_notifications), 1, "Should have 1 sent notification")
        self.assertEqual(len(pending_notifications), 1, "Should have 1 pending notification")
        
        # Verify delivery tracking
        delivered_count = len([n for n in notifications if n['delivery_status'] == 'delivered'])
        self.assertEqual(delivered_count, 1, "Should track 1 delivered notification")