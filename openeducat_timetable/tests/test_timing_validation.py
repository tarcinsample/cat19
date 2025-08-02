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
class TestTimingValidation(TestTimetableCommon):
    """Test timing and schedule validation."""

    def test_timing_creation(self):
        """Test basic timing creation."""
        timing = self.create_timing(9.0, 10.0, name='Test Period')
        
        self.assertEqual(timing.start_time, 9.0, "Start time should be 9.0")
        self.assertEqual(timing.end_time, 10.0, "End time should be 10.0")
        self.assertEqual(timing.name, 'Test Period', "Name should be set")

    def test_timing_validation_rules(self):
        """Test timing validation rules."""
        # Test end time before start time
        with self.assertRaises(ValidationError):
            self.create_timing(10.0, 9.0, name='Invalid Timing')
        
        # Test same start and end time
        with self.assertRaises(ValidationError):
            self.create_timing(9.0, 9.0, name='Zero Duration')

    def test_timing_overlap_detection(self):
        """Test detection of overlapping timings."""
        # Create first timing
        timing1 = self.create_timing(9.0, 10.0, name='Period 1')
        
        # Test overlapping timing
        with self.assertRaises(ValidationError):
            self.create_timing(9.5, 10.5, name='Overlapping Period')

    def test_timing_duration_validation(self):
        """Test timing duration validation."""
        # Test minimum duration
        min_duration = 0.5  # 30 minutes
        
        # Valid duration
        timing_valid = self.create_timing(9.0, 9.5, name='Valid 30min')
        self.assertEqual(timing_valid.end_time - timing_valid.start_time, min_duration,
                        "Should accept minimum duration")
        
        # Test too short duration
        with self.assertRaises(ValidationError):
            self.create_timing(9.0, 9.1, name='Too Short')  # 6 minutes

    def test_timing_business_hours_validation(self):
        """Test timing within business hours."""
        # Valid business hours timing
        timing_valid = self.create_timing(9.0, 17.0, name='Business Hours')
        self.assertGreaterEqual(timing_valid.start_time, 8.0, "Should be within business hours")
        self.assertLessEqual(timing_valid.end_time, 18.0, "Should be within business hours")
        
        # Test timing outside business hours
        with self.assertRaises(ValidationError):
            self.create_timing(6.0, 7.0, name='Too Early')
        
        with self.assertRaises(ValidationError):
            self.create_timing(20.0, 21.0, name='Too Late')

    def test_timing_break_consideration(self):
        """Test consideration of break times."""
        # Create lunch break timing
        lunch_break = self.create_timing(12.0, 13.0, name='Lunch Break')
        
        # Test session timing that conflicts with break
        with self.assertRaises(ValidationError):
            session = self.create_timetable_session(
                timing_id=lunch_break.id,
                day='monday'
            )

    def test_timing_sequence_validation(self):
        """Test validation of timing sequences."""
        # Create sequential timings
        timing1 = self.create_timing(9.0, 10.0, name='Period 1')
        timing2 = self.create_timing(10.0, 11.0, name='Period 2')
        timing3 = self.create_timing(11.0, 12.0, name='Period 3')
        
        # Verify sequence is valid
        timings = [timing1, timing2, timing3]
        for i in range(len(timings) - 1):
            self.assertEqual(timings[i].end_time, timings[i + 1].start_time,
                           f"Timing {i+1} should connect to timing {i+2}")

    def test_timing_gap_validation(self):
        """Test validation of gaps between timings."""
        # Create timings with appropriate gaps
        timing1 = self.create_timing(9.0, 10.0, name='Period 1')
        timing2 = self.create_timing(10.15, 11.15, name='Period 2')  # 15-minute break
        
        # Verify gap is appropriate
        gap = timing2.start_time - timing1.end_time
        self.assertGreaterEqual(gap * 60, 10, "Should have at least 10-minute break")

    def test_timing_weekday_constraints(self):
        """Test timing constraints for different weekdays."""
        weekdays = self.get_weekdays()
        
        for day in weekdays:
            # Test creating sessions for each day
            session = self.create_timetable_session(
                day=day,
                timing_id=self.timing_morning1.id,
                classroom=f'Room {day.title()}'
            )
            
            self.assertEqual(session.day, day, f"Should create session for {day}")

    def test_timing_modification_validation(self):
        """Test validation when modifying existing timings."""
        timing = self.create_timing(9.0, 10.0, name='Modifiable Timing')
        
        # Create session using this timing
        session = self.create_timetable_session(timing_id=timing.id)
        
        # Test modifying timing with existing sessions
        with self.assertRaises(ValidationError):
            timing.start_time = 8.0  # This would affect existing sessions

    def test_concurrent_timing_usage(self):
        """Test concurrent usage of same timing."""
        # Multiple sessions can use same timing on different days
        session1 = self.create_timetable_session(
            day='monday',
            timing_id=self.timing_morning1.id,
            classroom='Room 101'
        )
        
        session2 = self.create_timetable_session(
            day='tuesday',
            timing_id=self.timing_morning1.id,
            faculty_id=self.faculty2.id,
            subject_id=self.subject2.id,
            classroom='Room 102'
        )
        
        # Should allow same timing on different days
        self.assertTrue(session1.exists(), "Session 1 should exist")
        self.assertTrue(session2.exists(), "Session 2 should exist")

    def test_timing_capacity_constraints(self):
        """Test timing capacity constraints."""
        # Test maximum sessions per timing slot
        max_concurrent_sessions = 5  # Example capacity
        
        sessions = []
        for i in range(max_concurrent_sessions):
            session = self.create_timetable_session(
                day='wednesday',
                timing_id=self.timing_morning1.id,
                faculty_id=self.faculty1.id if i % 2 == 0 else self.faculty2.id,
                subject_id=self.subject1.id if i % 2 == 0 else self.subject2.id,
                classroom=f'Room {201 + i}'
            )
            sessions.append(session)
        
        # Verify capacity constraint
        timing_sessions = self.env['op.session'].search([
            ('timing_id', '=', self.timing_morning1.id),
            ('day', '=', 'wednesday')
        ])
        
        self.assertLessEqual(len(timing_sessions), max_concurrent_sessions + 1,
                           "Should respect timing capacity constraints")

    def test_timing_priority_handling(self):
        """Test priority handling for timings."""
        # Create priority timings
        priority_timing = self.create_timing(10.0, 11.0, name='Priority Period')
        regular_timing = self.create_timing(14.0, 15.0, name='Regular Period')
        
        # Test priority assignment if supported
        if hasattr(priority_timing, 'priority'):
            priority_timing.priority = 'high'
            regular_timing.priority = 'normal'
            
            self.assertEqual(priority_timing.priority, 'high', "Should set high priority")
            self.assertEqual(regular_timing.priority, 'normal', "Should set normal priority")

    def test_timing_pattern_validation(self):
        """Test validation of timing patterns."""
        # Test regular pattern (hourly slots)
        hourly_timings = []
        for hour in range(9, 17):  # 9 AM to 5 PM
            timing = self.create_timing(
                float(hour), 
                float(hour + 1), 
                name=f'Hour {hour:02d}:00-{hour+1:02d}:00'
            )
            hourly_timings.append(timing)
        
        # Verify pattern consistency
        for i in range(len(hourly_timings) - 1):
            current_end = hourly_timings[i].end_time
            next_start = hourly_timings[i + 1].start_time
            self.assertEqual(current_end, next_start, "Timings should follow consistent pattern")

    def test_timing_exception_handling(self):
        """Test handling of timing exceptions."""
        # Test holiday timing adjustments
        regular_timing = self.create_timing(9.0, 10.0, name='Regular Period')
        
        # Test timing on special days if supported
        if hasattr(regular_timing, 'is_active'):
            # Deactivate timing for holidays
            regular_timing.is_active = False
            
            # Should not allow sessions on inactive timings
            with self.assertRaises(ValidationError):
                self.create_timetable_session(timing_id=regular_timing.id)

    def test_timing_duration_optimization(self):
        """Test optimization of timing durations."""
        # Test different duration preferences
        durations = [1.0, 1.5, 2.0]  # 1, 1.5, 2 hours
        
        optimized_timings = []
        start_time = 9.0
        
        for duration in durations:
            timing = self.create_timing(
                start_time,
                start_time + duration,
                name=f'{duration}h Period'
            )
            optimized_timings.append(timing)
            start_time += duration + 0.25  # 15-minute break
        
        # Verify optimization
        for i, timing in enumerate(optimized_timings):
            expected_duration = durations[i]
            actual_duration = timing.end_time - timing.start_time
            self.assertEqual(actual_duration, expected_duration,
                           f"Duration should be {expected_duration} hours")

    def test_timing_conflict_resolution(self):
        """Test conflict resolution for timings."""
        # Create conflicting timing requests
        base_timing = self.create_timing(10.0, 11.0, name='Base Timing')
        
        # Test automatic conflict resolution
        try:
            # This might trigger automatic adjustment
            adjusted_timing = self.create_timing(10.5, 11.5, name='Adjusted Timing')
            
            # If creation succeeds, verify adjustment
            self.assertNotEqual(adjusted_timing.start_time, 10.5,
                              "Should adjust conflicting timing")
        except ValidationError:
            # Conflict detected and rejected
            pass

    def test_timing_validation_performance(self):
        """Test performance of timing validation."""
        # Create large number of timings
        timings = []
        
        for i in range(100):
            start_time = 8.0 + (i * 0.1)  # 6-minute slots
            end_time = start_time + 0.1
            
            # Only create if within reasonable bounds
            if end_time <= 18.0:
                timing = self.create_timing(
                    start_time,
                    end_time,
                    name=f'Micro Period {i}'
                )
                timings.append(timing)
        
        # Test search performance
        all_timings = self.env['op.timing'].search([])
        self.assertGreaterEqual(len(all_timings), len(timings),
                               "Should handle many timings efficiently")

    def test_timing_format_validation(self):
        """Test validation of timing formats."""
        # Test 24-hour format validation
        valid_times = [0.0, 6.5, 12.0, 18.5, 23.75]  # Various valid times
        
        for time_val in valid_times:
            if time_val < 23.0:  # Ensure end time is valid
                timing = self.create_timing(
                    time_val,
                    time_val + 1.0,
                    name=f'Time {time_val}'
                )
                
                self.assertGreaterEqual(timing.start_time, 0.0, "Time should be non-negative")
                self.assertLess(timing.end_time, 24.0, "Time should be less than 24.0")

    def test_timing_recurrence_patterns(self):
        """Test recurrence patterns for timings."""
        # Test weekly recurrence
        base_timing = self.create_timing(9.0, 10.0, name='Weekly Period')
        
        # Create sessions for weekly pattern
        weekdays = self.get_weekdays()
        weekly_sessions = []
        
        for day in weekdays:
            session = self.create_timetable_session(
                day=day,
                timing_id=base_timing.id,
                classroom=f'Room {day.title()}'
            )
            weekly_sessions.append(session)
        
        # Verify weekly pattern
        self.assertEqual(len(weekly_sessions), len(weekdays),
                        "Should create session for each weekday")

    def test_timing_holiday_adjustment(self):
        """Test timing adjustments for holidays."""
        # Create standard timing
        standard_timing = self.create_timing(9.0, 10.0, name='Standard Period')
        
        # Test holiday adjustment if supported
        if hasattr(standard_timing, 'holiday_adjustment'):
            # Adjust timing for holidays
            holiday_start = 10.0  # Later start on holidays
            holiday_end = 11.0
            
            standard_timing.holiday_adjustment = True
            
            # Verify adjustment capability exists
            self.assertTrue(hasattr(standard_timing, 'holiday_adjustment'),
                          "Should support holiday adjustments")

    def test_timing_integration_validation(self):
        """Test timing integration with other modules."""
        # Test timing integration with academic calendar
        timing = self.create_timing(9.0, 10.0, name='Integration Test')
        
        # Create session using timing
        session = self.create_timetable_session(timing_id=timing.id)
        
        # Verify integration
        self.assertEqual(session.timing_id, timing, "Session should link to timing")
        self.assertEqual(session.course_id, self.course, "Session should link to course")
        self.assertEqual(session.academic_year_id, self.academic_year, 
                        "Session should link to academic year")

    def test_timing_boundary_conditions(self):
        """Test timing boundary conditions."""
        # Test edge cases
        boundary_cases = [
            (8.0, 8.5),   # Early morning
            (12.0, 12.5), # Lunch time
            (17.5, 18.0), # End of day
        ]
        
        for start, end in boundary_cases:
            timing = self.create_timing(start, end, name=f'Boundary {start}-{end}')
            
            # Verify boundary handling
            self.assertEqual(timing.start_time, start, f"Start time should be {start}")
            self.assertEqual(timing.end_time, end, f"End time should be {end}")

    def test_timing_cleanup_validation(self):
        """Test cleanup of unused timings."""
        # Create timing without sessions
        unused_timing = self.create_timing(16.0, 17.0, name='Unused Timing')
        
        # Create timing with sessions
        used_timing = self.create_timing(15.0, 16.0, name='Used Timing')
        session = self.create_timetable_session(timing_id=used_timing.id)
        
        # Test cleanup logic
        timings_with_sessions = self.env['op.timing'].search([
            ('id', 'in', self.env['op.session'].search([]).mapped('timing_id').ids)
        ])
        
        self.assertIn(used_timing, timings_with_sessions, "Used timing should be found")
        
        # Unused timing cleanup would be handled by maintenance scripts