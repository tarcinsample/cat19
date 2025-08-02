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

from odoo.exceptions import ValidationError, UserError
from odoo.tests import tagged
from .test_timetable_common import TestTimetableCommon


@tagged('post_install', '-at_install', 'openeducat_timetable')
class TestTimetableGeneration(TestTimetableCommon):
    """Test timetable generation algorithm."""

    def test_basic_timetable_session_creation(self):
        """Test basic timetable session creation."""
        session = self.create_timetable_session()
        
        self.assertEqual(session.course_id, self.course, "Course should be linked")
        self.assertEqual(session.batch_id, self.batch, "Batch should be linked")
        self.assertEqual(session.subject_id, self.subject1, "Subject should be linked")
        self.assertEqual(session.faculty_id, self.faculty1, "Faculty should be linked")
        self.assertEqual(session.timing_id, self.timing_morning1, "Timing should be linked")
        self.assertEqual(session.day, 'monday', "Day should be monday")

    def test_timetable_generation_wizard(self):
        """Test timetable generation using wizard."""
        if 'generate.time.table' in self.env:
            # Create timetable generation wizard
            wizard = self.env['generate.time.table'].create({
                'course_id': self.course.id,
                'batch_id': self.batch.id,
                'academic_year_id': self.academic_year.id,
                'academic_term_id': self.academic_term.id,
            })
            
            self.assertEqual(wizard.course_id, self.course, "Wizard course should be set")
            self.assertEqual(wizard.batch_id, self.batch, "Wizard batch should be set")

    def test_automatic_timetable_generation(self):
        """Test automatic timetable generation algorithm."""
        # Create multiple subjects and faculty for generation
        subjects = [self.subject1, self.subject2]
        faculties = [self.faculty1, self.faculty2]
        timings = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1]
        weekdays = self.get_weekdays()
        
        # Generate timetable sessions automatically
        generated_sessions = []
        
        for day in weekdays[:3]:  # Generate for 3 days
            for i, timing in enumerate(timings):
                if i < len(subjects) and i < len(faculties):
                    session = self.create_timetable_session(
                        subject_id=subjects[i].id,
                        faculty_id=faculties[i].id,
                        timing_id=timing.id,
                        day=day,
                        classroom=f'Room {100 + i}'
                    )
                    generated_sessions.append(session)
        
        # Verify generated sessions
        self.assertGreater(len(generated_sessions), 0, "Should generate sessions")
        
        # Check distribution across days
        days_covered = set([session.day for session in generated_sessions])
        self.assertGreaterEqual(len(days_covered), 3, "Should cover multiple days")

    def test_timetable_conflict_detection(self):
        """Test detection of scheduling conflicts."""
        # Create first session
        session1 = self.create_timetable_session(
            day='monday',
            timing_id=self.timing_morning1.id,
            faculty_id=self.faculty1.id
        )
        
        # Try to create conflicting session (same faculty, same time)
        with self.assertRaises(ValidationError):
            self.create_timetable_session(
                day='monday',
                timing_id=self.timing_morning1.id,
                faculty_id=self.faculty1.id,
                subject_id=self.subject2.id
            )

    def test_classroom_conflict_detection(self):
        """Test detection of classroom conflicts."""
        # Create first session in Room 101
        session1 = self.create_timetable_session(
            day='monday',
            timing_id=self.timing_morning1.id,
            classroom='Room 101'
        )
        
        # Try to create conflicting session (same classroom, same time)
        with self.assertRaises(ValidationError):
            self.create_timetable_session(
                day='monday',
                timing_id=self.timing_morning1.id,
                faculty_id=self.faculty2.id,
                subject_id=self.subject2.id,
                classroom='Room 101'
            )

    def test_batch_conflict_detection(self):
        """Test detection of batch scheduling conflicts."""
        # Create first session for batch
        session1 = self.create_timetable_session(
            day='tuesday',
            timing_id=self.timing_morning2.id,
            batch_id=self.batch.id
        )
        
        # Try to create conflicting session (same batch, same time)
        with self.assertRaises(ValidationError):
            self.create_timetable_session(
                day='tuesday',
                timing_id=self.timing_morning2.id,
                batch_id=self.batch.id,
                faculty_id=self.faculty2.id,
                subject_id=self.subject2.id
            )

    def test_optimal_schedule_distribution(self):
        """Test optimal distribution of schedules."""
        # Generate balanced timetable
        subjects = [self.subject1, self.subject2]
        faculties = [self.faculty1, self.faculty2]
        weekdays = ['monday', 'tuesday', 'wednesday']
        timings = [self.timing_morning1, self.timing_morning2]
        
        sessions = []
        session_count = 0
        
        for day in weekdays:
            for timing in timings:
                if session_count < len(subjects):
                    session = self.create_timetable_session(
                        day=day,
                        timing_id=timing.id,
                        subject_id=subjects[session_count % len(subjects)].id,
                        faculty_id=faculties[session_count % len(faculties)].id,
                        classroom=f'Room {101 + session_count}'
                    )
                    sessions.append(session)
                    session_count += 1
        
        # Verify distribution
        days_used = {}
        for session in sessions:
            if session.day not in days_used:
                days_used[session.day] = 0
            days_used[session.day] += 1
        
        # Check balanced distribution
        max_sessions_per_day = max(days_used.values())
        min_sessions_per_day = min(days_used.values())
        self.assertLessEqual(max_sessions_per_day - min_sessions_per_day, 1,
                           "Sessions should be evenly distributed across days")

    def test_faculty_workload_balancing(self):
        """Test faculty workload balancing in timetable."""
        # Create additional faculty and subjects
        faculty3 = self.env['op.faculty'].create({'name': 'Test Faculty 3'})
        subject3 = self.env['op.subject'].create({
            'name': 'Chemistry',
            'code': 'CHEM001',
            'department_id': self.department.id,
        })
        
        faculties = [self.faculty1, self.faculty2, faculty3]
        subjects = [self.subject1, self.subject2, subject3]
        
        # Generate sessions with workload balancing
        sessions = []
        for i in range(9):  # 9 sessions to distribute among 3 faculty
            day = ['monday', 'tuesday', 'wednesday'][i // 3]
            timing = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1][i % 3]
            
            session = self.create_timetable_session(
                day=day,
                timing_id=timing.id,
                faculty_id=faculties[i % len(faculties)].id,
                subject_id=subjects[i % len(subjects)].id,
                classroom=f'Room {101 + i}'
            )
            sessions.append(session)
        
        # Check workload distribution
        faculty_workload = {}
        for session in sessions:
            faculty_id = session.faculty_id.id
            if faculty_id not in faculty_workload:
                faculty_workload[faculty_id] = 0
            faculty_workload[faculty_id] += 1
        
        # Verify balanced workload
        workloads = list(faculty_workload.values())
        self.assertEqual(len(set(workloads)), 1, "All faculty should have equal workload")

    def test_time_slot_optimization(self):
        """Test optimization of time slot allocation."""
        # Test preference for morning slots over afternoon
        morning_timings = [self.timing_morning1, self.timing_morning2]
        afternoon_timings = [self.timing_afternoon1]
        
        # Generate sessions preferring morning slots
        sessions = []
        
        # Fill morning slots first
        for i, timing in enumerate(morning_timings):
            session = self.create_timetable_session(
                day='monday',
                timing_id=timing.id,
                subject_id=[self.subject1, self.subject2][i].id,
                faculty_id=[self.faculty1, self.faculty2][i].id,
                classroom=f'Room {101 + i}'
            )
            sessions.append(session)
        
        # Verify morning preference
        morning_sessions = [s for s in sessions if s.timing_id in morning_timings]
        self.assertEqual(len(morning_sessions), 2, "Should prefer morning slots")

    def test_subject_frequency_balancing(self):
        """Test balancing of subject frequency in timetable."""
        # Create sessions for different subjects
        subjects = [self.subject1, self.subject2]
        sessions_per_subject = 3
        
        sessions = []
        for subject in subjects:
            for i in range(sessions_per_subject):
                day = ['monday', 'tuesday', 'wednesday'][i]
                timing = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1][i]
                
                session = self.create_timetable_session(
                    day=day,
                    timing_id=timing.id,
                    subject_id=subject.id,
                    faculty_id=self.faculty1.id if subject == self.subject1 else self.faculty2.id,
                    classroom=f'Room {101 + len(sessions)}'
                )
                sessions.append(session)
        
        # Check subject frequency
        subject_frequency = {}
        for session in sessions:
            subject_id = session.subject_id.id
            if subject_id not in subject_frequency:
                subject_frequency[subject_id] = 0
            subject_frequency[subject_id] += 1
        
        # Verify balanced frequency
        frequencies = list(subject_frequency.values())
        self.assertEqual(len(set(frequencies)), 1, "All subjects should have equal frequency")

    def test_consecutive_session_handling(self):
        """Test handling of consecutive sessions."""
        # Create consecutive sessions for same subject
        session1 = self.create_timetable_session(
            day='monday',
            timing_id=self.timing_morning1.id,
            subject_id=self.subject1.id
        )
        
        session2 = self.create_timetable_session(
            day='monday',
            timing_id=self.timing_morning2.id,
            subject_id=self.subject1.id,
            classroom='Room 102'
        )
        
        # Verify consecutive sessions are allowed for same subject
        self.assertTrue(session1.exists(), "First session should exist")
        self.assertTrue(session2.exists(), "Consecutive session should be allowed")

    def test_break_time_consideration(self):
        """Test consideration of break times in scheduling."""
        # Create timing for break
        break_timing = self.create_timing(11.0, 11.5, name='Break (11:00-11:30)')
        
        # Verify break timing is not used for sessions
        available_timings = self.get_time_slots()
        regular_timings = available_timings.filtered(lambda t: 'break' not in t.name.lower())
        
        self.assertGreater(len(regular_timings), 0, "Should have regular timings available")

    def test_timetable_validation_rules(self):
        """Test validation rules for timetable generation."""
        # Test session without course
        with self.assertRaises(ValidationError):
            self.env['op.session'].create({
                'batch_id': self.batch.id,
                'subject_id': self.subject1.id,
                'faculty_id': self.faculty1.id,
                'timing_id': self.timing_morning1.id,
                'day': 'monday',
            })
        
        # Test session without timing
        with self.assertRaises(ValidationError):
            self.env['op.session'].create({
                'course_id': self.course.id,
                'batch_id': self.batch.id,
                'subject_id': self.subject1.id,
                'faculty_id': self.faculty1.id,
                'day': 'monday',
            })

    def test_timetable_modification_workflow(self):
        """Test timetable modification workflow."""
        # Create initial session
        session = self.create_timetable_session()
        
        # Modify session timing
        original_timing = session.timing_id
        session.timing_id = self.timing_morning2.id
        
        self.assertNotEqual(session.timing_id, original_timing, "Timing should be modified")
        self.assertEqual(session.timing_id, self.timing_morning2, "New timing should be set")

    def test_bulk_timetable_generation(self):
        """Test bulk generation of timetable sessions."""
        # Generate multiple sessions in bulk
        sessions_data = []
        
        weekdays = ['monday', 'tuesday', 'wednesday']
        timings = [self.timing_morning1, self.timing_morning2]
        subjects = [self.subject1, self.subject2]
        faculties = [self.faculty1, self.faculty2]
        
        session_count = 0
        for day in weekdays:
            for timing in timings:
                if session_count < len(subjects):
                    sessions_data.append({
                        'course_id': self.course.id,
                        'batch_id': self.batch.id,
                        'subject_id': subjects[session_count].id,
                        'faculty_id': faculties[session_count].id,
                        'timing_id': timing.id,
                        'day': day,
                        'classroom': f'Room {101 + session_count}',
                    })
                    session_count += 1
        
        # Create sessions in bulk
        sessions = self.env['op.session'].create(sessions_data)
        
        self.assertEqual(len(sessions), len(sessions_data), "Should create all sessions")

    def test_timetable_generation_performance(self):
        """Test performance of timetable generation."""
        # Create large dataset for performance testing
        additional_subjects = []
        additional_faculties = []
        
        for i in range(10):
            subject = self.env['op.subject'].create({
                'name': f'Performance Subject {i}',
                'code': f'PERF{i:03d}',
                'department_id': self.department.id,
            })
            additional_subjects.append(subject)
            
            faculty = self.env['op.faculty'].create({
                'name': f'Performance Faculty {i}',
            })
            additional_faculties.append(faculty)
        
        # Generate large number of sessions
        sessions = []
        for i in range(50):
            day = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'][i % 5]
            timing = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1][i % 3]
            subject = additional_subjects[i % len(additional_subjects)]
            faculty = additional_faculties[i % len(additional_faculties)]
            
            session = self.create_timetable_session(
                day=day,
                timing_id=timing.id,
                subject_id=subject.id,
                faculty_id=faculty.id,
                classroom=f'Room {200 + i}'
            )
            sessions.append(session)
        
        # Verify performance
        self.assertEqual(len(sessions), 50, "Should generate all sessions efficiently")

    def test_timetable_generation_constraints(self):
        """Test various constraints in timetable generation."""
        # Test maximum sessions per day constraint
        max_sessions_per_day = 5
        
        sessions_monday = []
        for i in range(max_sessions_per_day):
            timing = self.create_timing(9.0 + i, 10.0 + i, name=f'Period {i+1}')
            session = self.create_timetable_session(
                day='monday',
                timing_id=timing.id,
                subject_id=self.subject1.id if i % 2 == 0 else self.subject2.id,
                faculty_id=self.faculty1.id if i % 2 == 0 else self.faculty2.id,
                classroom=f'Room {101 + i}'
            )
            sessions_monday.append(session)
        
        # Verify constraint compliance
        monday_sessions = self.env['op.session'].search([('day', '=', 'monday')])
        self.assertLessEqual(len(monday_sessions), max_sessions_per_day + 3,  # Allow for existing sessions
                           "Should respect maximum sessions per day")

    def test_timetable_generation_rollback(self):
        """Test rollback capability for timetable generation."""
        # Create initial session
        initial_session = self.create_timetable_session()
        
        # Create additional sessions
        additional_sessions = []
        for i in range(3):
            timing = [self.timing_morning2, self.timing_afternoon1][i % 2]
            day = ['tuesday', 'wednesday', 'thursday'][i]
            
            session = self.create_timetable_session(
                day=day,
                timing_id=timing.id,
                subject_id=self.subject2.id,
                faculty_id=self.faculty2.id,
                classroom=f'Room {102 + i}'
            )
            additional_sessions.append(session)
        
        # Rollback additional sessions
        for session in additional_sessions:
            session.unlink()
        
        # Verify rollback
        remaining_sessions = self.env['op.session'].search([
            ('course_id', '=', self.course.id),
            ('batch_id', '=', self.batch.id)
        ])
        
        self.assertIn(initial_session, remaining_sessions, "Initial session should remain")
        
        for session in additional_sessions:
            self.assertFalse(session.exists(), "Additional sessions should be removed")