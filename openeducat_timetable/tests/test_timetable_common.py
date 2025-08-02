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

from datetime import datetime, time, timedelta
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_timetable')
class TestTimetableCommon(TransactionCase):
    """Common test setup for timetable module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for timetable tests."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create academic year
        cls.academic_year = cls.env['op.academic.year'].create({
            'name': 'Test Year 2024-25',
            'code': 'TY24',
            'date_start': '2024-06-01',
            'date_stop': '2025-05-31',
        })
        
        # Create academic term
        cls.academic_term = cls.env['op.academic.term'].create({
            'name': 'Test Term 1',
            'code': 'TT1',
            'term_start_date': '2024-06-01',
            'term_end_date': '2024-12-31',
            'parent_id': cls.academic_year.id,
        })
        
        # Create department
        cls.department = cls.env['op.department'].create({
            'name': 'Test Department',
            'code': 'TD001',
        })
        
        # Create course
        cls.course = cls.env['op.course'].create({
            'name': 'Test Course',
            'code': 'TC001',
            'department_id': cls.department.id,
        })
        
        # Create batch
        cls.batch = cls.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'TB001',
            'course_id': cls.course.id,
            'start_date': '2024-06-01',
            'end_date': '2024-12-31',
        })
        
        # Create subjects
        cls.subject1 = cls.env['op.subject'].create({
            'name': 'Mathematics',
            'code': 'MATH001',
            'department_id': cls.department.id,
        })
        
        cls.subject2 = cls.env['op.subject'].create({
            'name': 'Physics',
            'code': 'PHY001',
            'department_id': cls.department.id,
        })
        
        # Create faculty
        cls.faculty1 = cls.env['op.faculty'].create({
            'name': 'Test Faculty 1',
        })
        
        cls.faculty2 = cls.env['op.faculty'].create({
            'name': 'Test Faculty 2',
        })
        
        # Create timings
        cls.timing_morning1 = cls.env['op.timing'].create({
            'start_time': 9.0,  # 9:00 AM
            'end_time': 10.0,   # 10:00 AM
            'name': 'Period 1 (9:00-10:00)',
        })
        
        cls.timing_morning2 = cls.env['op.timing'].create({
            'start_time': 10.0,  # 10:00 AM
            'end_time': 11.0,    # 11:00 AM
            'name': 'Period 2 (10:00-11:00)',
        })
        
        cls.timing_afternoon1 = cls.env['op.timing'].create({
            'start_time': 14.0,  # 2:00 PM
            'end_time': 15.0,    # 3:00 PM
            'name': 'Period 3 (14:00-15:00)',
        })

    def create_timetable_session(self, **kwargs):
        """Helper method to create timetable session."""
        vals = {
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'subject_id': self.subject1.id,
            'faculty_id': self.faculty1.id,
            'timing_id': self.timing_morning1.id,
            'day': 'monday',
            'classroom': 'Room 101',
        }
        vals.update(kwargs)
        return self.env['op.session'].create(vals)

    def create_timing(self, start_time, end_time, **kwargs):
        """Helper method to create timing."""
        vals = {
            'start_time': start_time,
            'end_time': end_time,
            'name': f'Period ({start_time:02.0f}:00-{end_time:02.0f}:00)',
        }
        vals.update(kwargs)
        return self.env['op.timing'].create(vals)

    def create_faculty_with_subjects(self, name, subject_ids=None, **kwargs):
        """Helper method to create faculty with subject assignments."""
        vals = {
            'name': name,
        }
        vals.update(kwargs)
        faculty = self.env['op.faculty'].create(vals)
        
        if subject_ids:
            # Link faculty to subjects if supported
            if hasattr(faculty, 'subject_ids'):
                faculty.subject_ids = [(6, 0, subject_ids)]
        
        return faculty

    def get_weekdays(self):
        """Get list of weekdays for timetable."""
        return ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    def get_time_slots(self):
        """Get available time slots."""
        return self.env['op.timing'].search([])

    def check_time_conflict(self, faculty, day, timing):
        """Check if faculty has time conflict."""
        existing_sessions = self.env['op.session'].search([
            ('faculty_id', '=', faculty.id),
            ('day', '=', day),
            ('timing_id', '=', timing.id),
        ])
        return len(existing_sessions) > 0
