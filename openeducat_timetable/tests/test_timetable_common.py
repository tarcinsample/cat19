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
import uuid
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
            
            'start_date': '2024-06-01',
            'end_date': '2025-05-31',
        })
        
        # Create academic term
        cls.academic_term = cls.env['op.academic.term'].create({
            'name': 'Test Term 1',
            
            'term_start_date': '2024-06-01',
            'term_end_date': '2024-12-31',
            'academic_year_id': cls.academic_year.id,
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
            'code': 'TB001_' + str(uuid.uuid4())[:8].replace('-', ''),
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
        
        # Create faculty with required fields
        faculty_partner1 = cls.env['res.partner'].create({
            'name': 'Test Faculty 1',
            'is_company': False,
        })
        cls.faculty1 = cls.env['op.faculty'].create({
            'partner_id': faculty_partner1.id,
            'first_name': 'Test',
            'last_name': 'Faculty1',
            'birth_date': '1980-01-01',
            'gender': 'male',
        })
        
        faculty_partner2 = cls.env['res.partner'].create({
            'name': 'Test Faculty 2',
            'is_company': False,
        })
        cls.faculty2 = cls.env['op.faculty'].create({
            'partner_id': faculty_partner2.id,
            'first_name': 'Test',
            'last_name': 'Faculty2',
            'birth_date': '1980-01-01',
            'gender': 'female',
        })
        
        # Create timings
        cls.timing_morning1 = cls.env['op.timing'].create({
            'name': 'Period 1 (9:00-10:00)',
            'hour': '9',
            'minute': '00',
            'am_pm': 'am',
            'duration': 1.0,
            'sequence': 1,
        })
        
        cls.timing_morning2 = cls.env['op.timing'].create({
            'name': 'Period 2 (10:00-11:00)',
            'hour': '10',
            'minute': '00',
            'am_pm': 'am',
            'duration': 1.0,
            'sequence': 2,
        })
        
        cls.timing_afternoon1 = cls.env['op.timing'].create({
            'name': 'Period 3 (2:00-3:00)',
            'hour': '2',
            'minute': '00',
            'am_pm': 'pm',
            'duration': 1.0,
            'sequence': 3,
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

    def create_timing(self, hour, minute='00', am_pm='am', duration=1.0, **kwargs):
        """Helper method to create timing."""
        vals = {
            'name': f'Period ({hour}:{minute} {am_pm.upper()})',
            'hour': str(hour),
            'minute': minute,
            'am_pm': am_pm,
            'duration': duration,
            'sequence': int(hour) if am_pm == 'am' else int(hour) + 12,
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
