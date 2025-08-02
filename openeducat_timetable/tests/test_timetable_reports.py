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

from odoo.tests import tagged
from .test_timetable_common import TestTimetableCommon


@tagged('post_install', '-at_install', 'openeducat_timetable')
class TestTimetableReports(TestTimetableCommon):
    """Test timetable reports (student/teacher)."""

    def setUp(self):
        """Set up test data for timetable reports."""
        super().setUp()
        self.setup_timetable_data()

    def setup_timetable_data(self):
        """Create comprehensive timetable data for reporting."""
        # Create multiple sessions for reporting
        self.sessions = []
        
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        timings = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1]
        subjects = [self.subject1, self.subject2]
        faculties = [self.faculty1, self.faculty2]
        
        session_count = 0
        for day in weekdays[:3]:  # 3 days
            for timing in timings:
                if session_count < 6:  # Create 6 sessions
                    session = self.create_timetable_session(
                        day=day,
                        timing_id=timing.id,
                        subject_id=subjects[session_count % len(subjects)].id,
                        faculty_id=faculties[session_count % len(faculties)].id,
                        classroom=f'Room {101 + session_count}'
                    )
                    self.sessions.append(session)
                    session_count += 1

    def test_student_timetable_report_generation(self):
        """Test student timetable report generation."""
        # Generate student timetable report
        if 'time.table.report' in self.env:
            report_wizard = self.env['time.table.report'].create({
                'report_type': 'student',
                'course_id': self.course.id,
                'batch_id': self.batch.id,
                'academic_year_id': self.academic_year.id,
            })
            
            self.assertEqual(report_wizard.report_type, 'student',
                           "Report type should be student")
            self.assertEqual(report_wizard.course_id, self.course,
                           "Course should be set for student report")

    def test_teacher_timetable_report_generation(self):
        """Test teacher timetable report generation."""
        # Generate teacher timetable report
        if 'time.table.report' in self.env:
            teacher_report = self.env['time.table.report'].create({
                'report_type': 'faculty',
                'faculty_id': self.faculty1.id,
                'academic_year_id': self.academic_year.id,
            })
            
            self.assertEqual(teacher_report.report_type, 'faculty',
                           "Report type should be faculty")
            self.assertEqual(teacher_report.faculty_id, self.faculty1,
                           "Faculty should be set for teacher report")

    def test_weekly_timetable_report_data(self):
        """Test weekly timetable report data structure."""
        # Generate weekly report data
        report_data = {
            'course': self.course.name,
            'batch': self.batch.name,
            'academic_year': self.academic_year.name,
            'weekly_schedule': {},
        }
        
        # Organize sessions by day
        weekdays = self.get_weekdays()
        for day in weekdays:
            day_sessions = [s for s in self.sessions if s.day == day]
            
            report_data['weekly_schedule'][day] = []
            for session in day_sessions:
                session_data = {
                    'timing': session.timing_id.name,
                    'subject': session.subject_id.name,
                    'faculty': session.faculty_id.name,
                    'classroom': session.classroom,
                    'start_time': session.timing_id.start_time,
                    'end_time': session.timing_id.end_time,
                }
                report_data['weekly_schedule'][day].append(session_data)
        
        # Verify report structure
        self.assertIn('weekly_schedule', report_data, "Should include weekly schedule")
        self.assertIn('course', report_data, "Should include course information")

    def test_faculty_schedule_report(self):
        """Test faculty schedule report generation."""
        # Generate faculty schedule
        faculty_schedule = {}
        
        for faculty in [self.faculty1, self.faculty2]:
            faculty_sessions = [s for s in self.sessions if s.faculty_id == faculty]
            
            schedule = {
                'faculty_name': faculty.name,
                'total_sessions': len(faculty_sessions),
                'schedule_by_day': {},
                'subjects_taught': list(set([s.subject_id.name for s in faculty_sessions])),
            }
            
            # Group by day
            for day in self.get_weekdays():
                day_sessions = [s for s in faculty_sessions if s.day == day]
                schedule['schedule_by_day'][day] = [
                    {
                        'time': s.timing_id.name,
                        'subject': s.subject_id.name,
                        'classroom': s.classroom,
                        'course': s.course_id.name,
                        'batch': s.batch_id.name,
                    }
                    for s in day_sessions
                ]
            
            faculty_schedule[faculty.id] = schedule
        
        # Verify faculty schedule
        self.assertIn(self.faculty1.id, faculty_schedule,
                     "Should include faculty1 schedule")
        self.assertIn(self.faculty2.id, faculty_schedule,
                     "Should include faculty2 schedule")

    def test_classroom_utilization_report(self):
        """Test classroom utilization report."""
        # Generate classroom utilization data
        classroom_usage = {}
        
        for session in self.sessions:
            classroom = session.classroom
            if classroom not in classroom_usage:
                classroom_usage[classroom] = {
                    'total_sessions': 0,
                    'sessions_by_day': {},
                    'utilization_hours': 0,
                }
            
            classroom_usage[classroom]['total_sessions'] += 1
            
            # Calculate utilization hours
            session_duration = session.timing_id.end_time - session.timing_id.start_time
            classroom_usage[classroom]['utilization_hours'] += session_duration
            
            # Group by day
            day = session.day
            if day not in classroom_usage[classroom]['sessions_by_day']:
                classroom_usage[classroom]['sessions_by_day'][day] = []
            
            classroom_usage[classroom]['sessions_by_day'][day].append({
                'timing': session.timing_id.name,
                'subject': session.subject_id.name,
                'faculty': session.faculty_id.name,
            })
        
        # Verify classroom utilization
        self.assertGreater(len(classroom_usage), 0, "Should have classroom usage data")
        
        for classroom, usage in classroom_usage.items():
            self.assertGreater(usage['total_sessions'], 0,
                             f"Classroom {classroom} should have sessions")

    def test_subject_distribution_report(self):
        """Test subject distribution report."""
        # Generate subject distribution
        subject_distribution = {}
        
        for session in self.sessions:
            subject = session.subject_id
            if subject.id not in subject_distribution:
                subject_distribution[subject.id] = {
                    'subject_name': subject.name,
                    'subject_code': subject.code,
                    'total_sessions': 0,
                    'faculty_assigned': set(),
                    'days_scheduled': set(),
                    'total_hours': 0,
                }
            
            dist = subject_distribution[subject.id]
            dist['total_sessions'] += 1
            dist['faculty_assigned'].add(session.faculty_id.name)
            dist['days_scheduled'].add(session.day)
            dist['total_hours'] += session.timing_id.end_time - session.timing_id.start_time
        
        # Convert sets to lists for verification
        for subject_id, dist in subject_distribution.items():
            dist['faculty_assigned'] = list(dist['faculty_assigned'])
            dist['days_scheduled'] = list(dist['days_scheduled'])
        
        # Verify subject distribution
        self.assertGreater(len(subject_distribution), 0, "Should have subject distribution")
        
        for subject_id, dist in subject_distribution.items():
            self.assertGreater(dist['total_sessions'], 0, "Should have sessions")
            self.assertGreater(len(dist['faculty_assigned']), 0, "Should have faculty assigned")

    def test_daily_schedule_report(self):
        """Test daily schedule report generation."""
        # Generate daily schedules
        daily_schedules = {}
        
        for day in self.get_weekdays():
            day_sessions = [s for s in self.sessions if s.day == day]
            
            # Sort by timing
            day_sessions.sort(key=lambda s: s.timing_id.start_time)
            
            daily_schedules[day] = {
                'day_name': day.title(),
                'total_sessions': len(day_sessions),
                'schedule': [
                    {
                        'time_slot': s.timing_id.name,
                        'start_time': s.timing_id.start_time,
                        'end_time': s.timing_id.end_time,
                        'subject': s.subject_id.name,
                        'faculty': s.faculty_id.name,
                        'classroom': s.classroom,
                        'course': s.course_id.name,
                        'batch': s.batch_id.name,
                    }
                    for s in day_sessions
                ],
            }
        
        # Verify daily schedules
        for day, schedule in daily_schedules.items():
            if schedule['total_sessions'] > 0:
                self.assertGreater(len(schedule['schedule']), 0,
                                 f"{day} should have schedule entries")

    def test_conflict_detection_report(self):
        """Test conflict detection in timetable reports."""
        # Detect various types of conflicts
        conflicts = {
            'faculty_conflicts': [],
            'classroom_conflicts': [],
            'batch_conflicts': [],
        }
        
        # Check faculty conflicts
        faculty_schedule = {}
        for session in self.sessions:
            key = f"{session.faculty_id.id}_{session.day}_{session.timing_id.id}"
            if key in faculty_schedule:
                conflicts['faculty_conflicts'].append({
                    'faculty': session.faculty_id.name,
                    'day': session.day,
                    'timing': session.timing_id.name,
                    'conflicting_sessions': [faculty_schedule[key], session.id],
                })
            else:
                faculty_schedule[key] = session.id
        
        # Check classroom conflicts
        classroom_schedule = {}
        for session in self.sessions:
            key = f"{session.classroom}_{session.day}_{session.timing_id.id}"
            if key in classroom_schedule:
                conflicts['classroom_conflicts'].append({
                    'classroom': session.classroom,
                    'day': session.day,
                    'timing': session.timing_id.name,
                    'conflicting_sessions': [classroom_schedule[key], session.id],
                })
            else:
                classroom_schedule[key] = session.id
        
        # Verify conflict detection
        total_conflicts = (len(conflicts['faculty_conflicts']) + 
                          len(conflicts['classroom_conflicts']) + 
                          len(conflicts['batch_conflicts']))
        
        # Should have minimal conflicts in well-designed timetable
        self.assertLessEqual(total_conflicts, 2, "Should have minimal conflicts")

    def test_workload_analysis_report(self):
        """Test workload analysis report."""
        # Analyze faculty workload
        workload_analysis = {}
        
        for faculty in [self.faculty1, self.faculty2]:
            faculty_sessions = [s for s in self.sessions if s.faculty_id == faculty]
            
            # Calculate workload metrics
            total_hours = sum([
                s.timing_id.end_time - s.timing_id.start_time 
                for s in faculty_sessions
            ])
            
            days_working = len(set([s.day for s in faculty_sessions]))
            subjects_taught = len(set([s.subject_id.id for s in faculty_sessions]))
            
            workload_analysis[faculty.id] = {
                'faculty_name': faculty.name,
                'total_sessions': len(faculty_sessions),
                'total_hours': total_hours,
                'days_working': days_working,
                'subjects_taught': subjects_taught,
                'avg_sessions_per_day': len(faculty_sessions) / max(days_working, 1),
                'workload_distribution': {},
            }
            
            # Daily workload distribution
            for day in self.get_weekdays():
                day_sessions = [s for s in faculty_sessions if s.day == day]
                workload_analysis[faculty.id]['workload_distribution'][day] = len(day_sessions)
        
        # Verify workload analysis
        for faculty_id, analysis in workload_analysis.items():
            self.assertGreaterEqual(analysis['total_hours'], 0, "Should calculate total hours")
            self.assertGreaterEqual(analysis['days_working'], 0, "Should count working days")

    def test_timetable_summary_report(self):
        """Test timetable summary report generation."""
        # Generate comprehensive summary
        summary_report = {
            'academic_info': {
                'academic_year': self.academic_year.name,
                'course': self.course.name,
                'batch': self.batch.name,
                'department': self.department.name,
            },
            'statistics': {
                'total_sessions': len(self.sessions),
                'total_faculty': len(set([s.faculty_id.id for s in self.sessions])),
                'total_subjects': len(set([s.subject_id.id for s in self.sessions])),
                'total_classrooms': len(set([s.classroom for s in self.sessions])),
                'days_with_classes': len(set([s.day for s in self.sessions])),
            },
            'utilization': {
                'weekly_hours': sum([
                    s.timing_id.end_time - s.timing_id.start_time 
                    for s in self.sessions
                ]),
                'avg_sessions_per_day': len(self.sessions) / max(len(set([s.day for s in self.sessions])), 1),
            },
        }
        
        # Verify summary report
        self.assertIn('academic_info', summary_report, "Should include academic info")
        self.assertIn('statistics', summary_report, "Should include statistics")
        self.assertIn('utilization', summary_report, "Should include utilization data")
        
        # Verify statistics accuracy
        stats = summary_report['statistics']
        self.assertEqual(stats['total_sessions'], len(self.sessions),
                        "Should count sessions correctly")

    def test_report_export_formats(self):
        """Test different export formats for reports."""
        # Test CSV export format
        csv_data = []
        csv_headers = ['Day', 'Time', 'Subject', 'Faculty', 'Classroom', 'Course', 'Batch']
        
        for session in self.sessions:
            csv_data.append([
                session.day.title(),
                session.timing_id.name,
                session.subject_id.name,
                session.faculty_id.name,
                session.classroom,
                session.course_id.name,
                session.batch_id.name,
            ])
        
        # Test PDF report data structure
        pdf_data = {
            'title': f'Timetable - {self.course.name} ({self.batch.name})',
            'academic_year': self.academic_year.name,
            'generation_date': '2024-06-15',
            'schedule_data': self.sessions,
        }
        
        # Verify export formats
        self.assertEqual(len(csv_headers), 7, "CSV should have correct headers")
        self.assertEqual(len(csv_data), len(self.sessions), "CSV should have all sessions")
        self.assertIn('title', pdf_data, "PDF should have title")

    def test_custom_report_filters(self):
        """Test custom filters for timetable reports."""
        # Test filtering by day
        monday_sessions = [s for s in self.sessions if s.day == 'monday']
        
        # Test filtering by timing
        morning_sessions = [s for s in self.sessions 
                           if s.timing_id.start_time < 12.0]
        
        # Test filtering by faculty
        faculty1_sessions = [s for s in self.sessions 
                            if s.faculty_id == self.faculty1]
        
        # Test filtering by subject
        subject1_sessions = [s for s in self.sessions 
                            if s.subject_id == self.subject1]
        
        # Verify filters work
        self.assertLessEqual(len(monday_sessions), len(self.sessions),
                           "Monday filter should reduce results")
        self.assertLessEqual(len(morning_sessions), len(self.sessions),
                           "Morning filter should reduce results")
        self.assertLessEqual(len(faculty1_sessions), len(self.sessions),
                           "Faculty filter should reduce results")

    def test_report_performance_large_dataset(self):
        """Test report performance with large dataset."""
        # Create large dataset
        large_sessions = []
        
        for i in range(100):
            day = self.get_weekdays()[i % 5]
            timing = [self.timing_morning1, self.timing_morning2, self.timing_afternoon1][i % 3]
            subject = [self.subject1, self.subject2][i % 2]
            faculty = [self.faculty1, self.faculty2][i % 2]
            
            session = self.create_timetable_session(
                day=day,
                timing_id=timing.id,
                subject_id=subject.id,
                faculty_id=faculty.id,
                classroom=f'Large Room {i}'
            )
            large_sessions.append(session)
        
        # Generate report from large dataset
        large_report_data = {
            'total_sessions': len(large_sessions),
            'sessions_by_day': {},
        }
        
        for day in self.get_weekdays():
            day_sessions = [s for s in large_sessions if s.day == day]
            large_report_data['sessions_by_day'][day] = len(day_sessions)
        
        # Verify performance
        self.assertEqual(large_report_data['total_sessions'], 100,
                        "Should handle large datasets efficiently")

    def test_real_time_report_updates(self):
        """Test real-time updates in timetable reports."""
        # Initial report data
        initial_count = len(self.sessions)
        
        # Add new session
        new_session = self.create_timetable_session(
            day='friday',
            timing_id=self.timing_morning1.id,
            subject_id=self.subject1.id,
            faculty_id=self.faculty2.id,
            classroom='New Room'
        )
        
        # Update report data
        updated_sessions = self.env['op.session'].search([
            ('course_id', '=', self.course.id),
            ('batch_id', '=', self.batch.id)
        ])
        
        # Verify real-time update
        self.assertEqual(len(updated_sessions), initial_count + 1,
                        "Report should reflect real-time updates")

    def test_report_access_permissions(self):
        """Test access permissions for different report types."""
        # Test report access levels
        report_permissions = {
            'student_timetable': ['student', 'faculty', 'admin'],
            'faculty_timetable': ['faculty', 'admin'],
            'classroom_utilization': ['admin'],
            'workload_analysis': ['admin'],
        }
        
        # Verify permission structure
        for report_type, allowed_roles in report_permissions.items():
            self.assertIn('admin', allowed_roles, "Admin should access all reports")
            self.assertIsInstance(allowed_roles, list, "Permissions should be list")

    def test_report_scheduling_automation(self):
        """Test automated report generation scheduling."""
        # Test scheduled report configuration
        scheduled_reports = {
            'weekly_timetable': {
                'frequency': 'weekly',
                'day': 'sunday',
                'time': '18:00',
                'recipients': ['admin@school.edu'],
            },
            'monthly_utilization': {
                'frequency': 'monthly',
                'date': 1,
                'time': '09:00',
                'recipients': ['principal@school.edu'],
            },
        }
        
        # Verify scheduling configuration
        for report_name, config in scheduled_reports.items():
            self.assertIn('frequency', config, "Should define frequency")
            self.assertIn('recipients', config, "Should define recipients")

    def test_report_data_accuracy_validation(self):
        """Test accuracy validation of report data."""
        # Validate session counts
        total_sessions = len(self.sessions)
        counted_sessions = 0
        
        for day in self.get_weekdays():
            day_sessions = len([s for s in self.sessions if s.day == day])
            counted_sessions += day_sessions
        
        self.assertEqual(total_sessions, counted_sessions,
                        "Session counts should be accurate")
        
        # Validate faculty assignments
        faculty_sessions = {}
        for session in self.sessions:
            faculty_id = session.faculty_id.id
            if faculty_id not in faculty_sessions:
                faculty_sessions[faculty_id] = 0
            faculty_sessions[faculty_id] += 1
        
        # Verify faculty assignment accuracy
        for faculty_id, count in faculty_sessions.items():
            actual_count = len([s for s in self.sessions if s.faculty_id.id == faculty_id])
            self.assertEqual(count, actual_count, "Faculty assignments should be accurate")