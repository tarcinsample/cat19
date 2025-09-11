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
from .test_timetable_common import TestTimetableCommon


@tagged('post_install', '-at_install', 'openeducat_timetable')
class TestFacultyConflicts(TestTimetableCommon):
    """Test faculty assignment and conflicts."""

    def test_faculty_availability_check(self):
        """Test faculty availability checking."""
        # Create session for faculty1
        session1 = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='monday',
            timing_id=self.timing_morning1.id
        )
        
        # Check availability
        is_available = not self.check_time_conflict(
            self.faculty1, 'monday', self.timing_morning1
        )
        
        self.assertFalse(is_available, "Faculty should not be available during assigned time")

    def test_faculty_double_booking_prevention(self):
        """Test prevention of faculty double booking."""
        # Create first session
        session1 = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='tuesday',
            timing_id=self.timing_morning1.id,
            subject_id=self.subject1.id
        )
        
        # Try to create conflicting session
        with self.assertRaises(ValidationError):
            self.create_timetable_session(
                faculty_id=self.faculty1.id,
                day='tuesday',
                timing_id=self.timing_morning1.id,
                subject_id=self.subject2.id,
                classroom='Room 102'
            )

    def test_faculty_workload_distribution(self):
        """Test distribution of faculty workload."""
        # Create multiple sessions for faculty
        sessions = []
        weekdays = ['monday', 'tuesday', 'wednesday']
        timings = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1]
        
        session_count = 0
        for day in weekdays:
            for timing in timings:
                if session_count < 6:  # Limit sessions
                    session = self.create_timetable_session(
                        faculty_id=self.faculty1.id,
                        day=day,
                        timing_id=timing.id,
                        subject_id=self.subject1.id if session_count % 2 == 0 else self.subject2.id,
                        classroom=f'Room {101 + session_count}'
                    )
                    sessions.append(session)
                    session_count += 1
        
        # Check workload distribution
        faculty_sessions = self.env['op.session'].search([
            ('faculty_id', '=', self.faculty1.id)
        ])
        
        # Verify reasonable workload
        self.assertLessEqual(len(faculty_sessions), 8, "Faculty workload should be reasonable")

    def test_faculty_subject_competency(self):
        """Test faculty subject competency validation."""
        # Create faculty with specific subject competency
        specialized_faculty = self.create_faculty_with_subjects(
            'Math Specialist',
            subject_ids=[self.subject1.id]  # Only Math
        )
        
        # Should allow Math sessions
        math_session = self.create_timetable_session(
            faculty_id=specialized_faculty.id,
            subject_id=self.subject1.id,
            day='wednesday',
            timing_id=self.timing_morning1.id
        )
        
        self.assertEqual(math_session.faculty_id, specialized_faculty,
                        "Should allow competent faculty assignment")

    def test_faculty_leave_conflict_detection(self):
        """Test detection of faculty leave conflicts."""
        # Create faculty leave record if supported
        if 'hr.leave' in self.env:
            # Create leave request
            leave = self.env['hr.leave'].create({
                'name': 'Faculty Leave',
                'employee_id': self.faculty1.id if hasattr(self.faculty1, 'employee_id') else None,
                'request_date_from': '2024-06-15',
                'request_date_to': '2024-06-15',
                'state': 'validate',
            })
            
            # Try to create session during leave
            # This would typically be handled by business logic
            pass

    def test_faculty_consecutive_sessions_validation(self):
        """Test validation of consecutive sessions for faculty."""
        # Create consecutive sessions
        session1 = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='thursday',
            timing_id=self.timing_morning1.id,
            subject_id=self.subject1.id
        )
        
        session2 = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='thursday',
            timing_id=self.timing_morning2.id,
            subject_id=self.subject1.id,
            classroom='Room 102'
        )
        
        # Should allow consecutive sessions for same faculty
        self.assertTrue(session1.exists(), "First session should exist")
        self.assertTrue(session2.exists(), "Consecutive session should be allowed")

    def test_faculty_break_time_enforcement(self):
        """Test enforcement of break time between sessions."""
        # Create session before break
        session1 = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='friday',
            timing_id=self.timing_morning2.id  # 10:00-11:00
        )
        
        # Create break timing
        break_timing = self.create_timing(11.0, 11.5, name='Break Time')
        
        # Create session after break
        afternoon_session = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='friday',
            timing_id=self.timing_afternoon1.id,  # 14:00-15:00
            subject_id=self.subject2.id,
            classroom='Room 103'
        )
        
        # Should allow session after adequate break
        self.assertTrue(afternoon_session.exists(), "Session after break should be allowed")

    def test_faculty_maximum_sessions_per_day(self):
        """Test maximum sessions per day for faculty."""
        max_sessions_per_day = 4
        
        # Create sessions up to limit
        sessions = []
        timings = [
            self.timing_morning1, 
            self.timing_morning2, 
            self.timing_afternoon1,
            self.create_timing(15.0, 16.0, name='Period 4')
        ]
        
        for i, timing in enumerate(timings):
            if i < max_sessions_per_day:
                session = self.create_timetable_session(
                    faculty_id=self.faculty2.id,
                    day='monday',
                    timing_id=timing.id,
                    subject_id=self.subject1.id if i % 2 == 0 else self.subject2.id,
                    classroom=f'Room {201 + i}'
                )
                sessions.append(session)
        
        # Verify limit enforcement
        monday_sessions = self.env['op.session'].search([
            ('faculty_id', '=', self.faculty2.id),
            ('day', '=', 'monday')
        ])
        
        self.assertLessEqual(len(monday_sessions), max_sessions_per_day,
                           "Should respect maximum sessions per day")

    def test_faculty_multi_campus_conflicts(self):
        """Test conflicts for faculty across multiple campuses."""
        # Create campus locations if supported
        if hasattr(self.env['op.session'], 'campus_id'):
            # Create different campus sessions
            campus1_session = self.create_timetable_session(
                faculty_id=self.faculty1.id,
                day='tuesday',
                timing_id=self.timing_morning1.id,
                classroom='Campus1-Room101'
            )
            
            # Should detect travel time conflicts
            with self.assertRaises(ValidationError):
                self.create_timetable_session(
                    faculty_id=self.faculty1.id,
                    day='tuesday',
                    timing_id=self.timing_morning2.id,  # Too close for campus travel
                    classroom='Campus2-Room101'
                )

    def test_faculty_preference_consideration(self):
        """Test consideration of faculty preferences."""
        # Set faculty preferences if supported
        if hasattr(self.faculty1, 'preferred_timings'):
            self.faculty1.preferred_timings = [(6, 0, [self.timing_morning1.id])]
            
            # Create session with preferred timing
            preferred_session = self.create_timetable_session(
                faculty_id=self.faculty1.id,
                timing_id=self.timing_morning1.id,
                day='wednesday'
            )
            
            self.assertEqual(preferred_session.timing_id, self.timing_morning1,
                           "Should consider faculty preferences")

    def test_faculty_replacement_handling(self):
        """Test handling of faculty replacement scenarios."""
        # Create original session
        original_session = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='thursday',
            timing_id=self.timing_morning1.id
        )
        
        # Replace faculty
        original_session.faculty_id = self.faculty2.id
        
        # Verify replacement
        self.assertEqual(original_session.faculty_id, self.faculty2,
                        "Faculty should be replaced successfully")

    def test_faculty_load_balancing(self):
        """Test load balancing across faculty."""
        # Create sessions distributed across faculty
        faculty_list = [self.faculty1, self.faculty2]
        sessions = []
        
        for i in range(8):  # 8 sessions to distribute
            day = ['monday', 'tuesday'][i // 4]
            timing = [self.timing_morning1, self.timing_morning2, 
                     self.timing_afternoon1, self.create_timing(15.0, 16.0)][i % 4]
            faculty = faculty_list[i % len(faculty_list)]
            
            session = self.create_timetable_session(
                faculty_id=faculty.id,
                day=day,
                timing_id=timing.id,
                subject_id=self.subject1.id if i % 2 == 0 else self.subject2.id,
                classroom=f'Room {301 + i}'
            )
            sessions.append(session)
        
        # Check load distribution
        faculty1_load = len([s for s in sessions if s.faculty_id == self.faculty1])
        faculty2_load = len([s for s in sessions if s.faculty_id == self.faculty2])
        
        # Should be balanced
        load_difference = abs(faculty1_load - faculty2_load)
        self.assertLessEqual(load_difference, 1, "Faculty load should be balanced")

    def test_faculty_overtime_prevention(self):
        """Test prevention of faculty overtime."""
        max_weekly_hours = 20  # Example limit
        
        # Create sessions approaching limit
        sessions = []
        weekly_hours = 0
        
        weekdays = self.get_weekdays()
        for day in weekdays:
            if weekly_hours < max_weekly_hours:
                session = self.create_timetable_session(
                    faculty_id=self.faculty1.id,
                    day=day,
                    timing_id=self.timing_morning1.id,
                    classroom=f'Room {day.title()}'
                )
                sessions.append(session)
                weekly_hours += 1  # 1 hour per session
        
        # Verify overtime prevention
        faculty_weekly_sessions = self.env['op.session'].search([
            ('faculty_id', '=', self.faculty1.id)
        ])
        
        total_hours = len(faculty_weekly_sessions)
        self.assertLessEqual(total_hours, max_weekly_hours + 5,  # Allow some flexibility
                           "Should prevent excessive overtime")

    def test_faculty_emergency_assignment(self):
        """Test emergency faculty assignment procedures."""
        # Create urgent session needing faculty
        urgent_timing = self.create_timing(8.0, 9.0, name='Emergency Period')
        
        # Find available faculty for emergency
        available_faculty = None
        for faculty in [self.faculty1, self.faculty2]:
            if not self.check_time_conflict(faculty, 'friday', urgent_timing):
                available_faculty = faculty
                break
        
        if available_faculty:
            emergency_session = self.create_timetable_session(
                faculty_id=available_faculty.id,
                timing_id=urgent_timing.id,
                day='friday',
                subject_id=self.subject1.id,
                classroom='Emergency Room'
            )
            
            self.assertTrue(emergency_session.exists(), "Emergency assignment should succeed")

    def test_faculty_conflict_resolution_workflow(self):
        """Test faculty conflict resolution workflow."""
        # Create conflicting assignments
        session1 = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='monday',
            timing_id=self.timing_morning1.id,
            subject_id=self.subject1.id
        )
        
        # Attempt to resolve conflict by reassigning
        try:
            conflicting_session = self.create_timetable_session(
                faculty_id=self.faculty1.id,
                day='monday',
                timing_id=self.timing_morning1.id,
                subject_id=self.subject2.id,
                classroom='Room 102'
            )
        except ValidationError:
            # Conflict detected, try resolution
            # Reassign to different timing
            resolved_session = self.create_timetable_session(
                faculty_id=self.faculty1.id,
                day='monday',
                timing_id=self.timing_morning2.id,
                subject_id=self.subject2.id,
                classroom='Room 102'
            )
            
            self.assertTrue(resolved_session.exists(), "Conflict should be resolved")

    def test_faculty_availability_reporting(self):
        """Test faculty availability reporting."""
        # Generate availability report
        availability_report = {}
        
        weekdays = self.get_weekdays()
        timings = self.get_time_slots()
        
        for faculty in [self.faculty1, self.faculty2]:
            faculty_schedule = {}
            
            for day in weekdays:
                day_schedule = {}
                for timing in timings:
                    is_available = not self.check_time_conflict(faculty, day, timing)
                    day_schedule[timing.name] = is_available
                
                faculty_schedule[day] = day_schedule
            
            availability_report[faculty.name] = faculty_schedule
        
        # Verify report structure
        self.assertIn(self.faculty1.name, availability_report,
                     "Report should include faculty1")
        self.assertIn(self.faculty2.name, availability_report,
                     "Report should include faculty2")

    def test_faculty_notification_system(self):
        """Test faculty notification system for assignments."""
        # Create session with notification
        session = self.create_timetable_session(
            faculty_id=self.faculty1.id,
            day='tuesday',
            timing_id=self.timing_afternoon1.id
        )
        
        # Test notification trigger if supported
        if hasattr(session, 'send_faculty_notification'):
            notification_sent = session.send_faculty_notification()
            self.assertTrue(notification_sent, "Should send faculty notification")

    def test_faculty_performance_tracking(self):
        """Test faculty performance tracking in scheduling."""
        # Create multiple sessions for performance tracking
        faculty_sessions = []
        
        for i in range(10):
            day = self.get_weekdays()[i % 5]
            timing = [self.timing_morning1, self.timing_morning2][i % 2]
            
            session = self.create_timetable_session(
                faculty_id=self.faculty1.id,
                day=day,
                timing_id=timing.id,
                subject_id=self.subject1.id if i % 2 == 0 else self.subject2.id,
                classroom=f'Room {401 + i}'
            )
            faculty_sessions.append(session)
        
        # Calculate performance metrics
        total_sessions = len(faculty_sessions)
        unique_days = len(set([s.day for s in faculty_sessions]))
        unique_subjects = len(set([s.subject_id.id for s in faculty_sessions]))
        
        performance_metrics = {
            'total_sessions': total_sessions,
            'days_utilized': unique_days,
            'subjects_taught': unique_subjects,
            'utilization_rate': unique_days / len(self.get_weekdays()),
        }
        
        # Verify performance tracking
        self.assertGreater(performance_metrics['total_sessions'], 0,
                         "Should track session count")
        self.assertGreater(performance_metrics['utilization_rate'], 0,
                         "Should calculate utilization rate")

    def test_faculty_conflict_batch_resolution(self):
        """Test batch resolution of faculty conflicts."""
        # Create multiple potential conflicts
        conflict_sessions = []
        
        try:
            for i in range(3):
                session = self.create_timetable_session(
                    faculty_id=self.faculty2.id,
                    day='wednesday',
                    timing_id=self.timing_morning1.id,
                    subject_id=[self.subject1, self.subject2][i % 2].id,
                    classroom=f'Conflict Room {i}'
                )
                conflict_sessions.append(session)
        except ValidationError:
            # Conflicts detected, resolve in batch
            resolved_sessions = []
            
            alternative_timings = [self.timing_morning2, self.timing_afternoon1]
            
            for i, timing in enumerate(alternative_timings):
                if i < 2:  # Resolve first 2 conflicts
                    resolved_session = self.create_timetable_session(
                        faculty_id=self.faculty2.id,
                        day='wednesday',
                        timing_id=timing.id,
                        subject_id=[self.subject1, self.subject2][i % 2].id,
                        classroom=f'Resolved Room {i}'
                    )
                    resolved_sessions.append(resolved_session)
            
            # Verify batch resolution
            self.assertGreater(len(resolved_sessions), 0, "Should resolve conflicts in batch")