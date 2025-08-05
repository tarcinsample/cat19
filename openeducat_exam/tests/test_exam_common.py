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
import uuid
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_exam')
class TestExamCommon(TransactionCase):
    """Common test setup for exam module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for exam tests."""
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
        
        # Create subjects
        cls.subject1 = cls.env['op.subject'].create({
            'name': 'Test Subject 1',
            'code': 'TS001',
        })
        
        cls.subject2 = cls.env['op.subject'].create({
            'name': 'Test Subject 2',
            'code': 'TS002',
        })
        
        # Create batch
        cls.batch = cls.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'TB001_' + str(uuid.uuid4())[:8].replace('-', ''),
            'course_id': cls.course.id,
            'start_date': '2024-06-01',
            'end_date': '2024-12-31',
        })
        
        # Create exam type
        cls.exam_type = cls.env['op.exam.type'].create({
            'name': 'Final Exam',
            'code': 'FINAL',
        })
        
        # Create faculty with required fields
        faculty_partner = cls.env['res.partner'].create({
            'name': 'Test Faculty',
            'is_company': False,
        })
        cls.faculty = cls.env['op.faculty'].create({
            'partner_id': faculty_partner.id,
            'first_name': 'Test',
            'last_name': 'Faculty',
            'birth_date': '1980-01-01',
            'gender': 'male',
            'faculty_subject_ids': [(6, 0, [cls.subject1.id, cls.subject2.id])],
        })
        
        # Create students with required partners
        partner1 = cls.env['res.partner'].create({
            'name': 'Test Student 1',
            'is_company': False,
        })
        cls.student1 = cls.env['op.student'].create({
            'partner_id': partner1.id,
            'first_name': 'Test',
            'last_name': 'Student1',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        partner2 = cls.env['res.partner'].create({
            'name': 'Test Student 2',
            'is_company': False,
        })
        cls.student2 = cls.env['op.student'].create({
            'partner_id': partner2.id,
            'first_name': 'Test',
            'last_name': 'Student2',
            'birth_date': '2000-02-02',
            'gender': 'f',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        # Create exam session
        cls.exam_session = cls.env['op.exam.session'].create({
            'name': 'Test Exam Session',
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'start_date': '2024-11-01',
            'end_date': '2024-11-30',
            'exam_type_id': cls.exam_type.id,
            'state': 'schedule',
        })
        
        # Create grade configuration
        cls.grade_config = cls.env['op.grade.configuration'].create({
            'name': 'Standard Grading',
            'result_line': [(0, 0, {
                'name': 'A+',
                'marks_range_from': 90,
                'marks_range_to': 100,
                'grade': 'A+',
            }), (0, 0, {
                'name': 'A',
                'marks_range_from': 80,
                'marks_range_to': 89,
                'grade': 'A',
            }), (0, 0, {
                'name': 'B',
                'marks_range_from': 70,
                'marks_range_to': 79,
                'grade': 'B',
            }), (0, 0, {
                'name': 'C',
                'marks_range_from': 60,
                'marks_range_to': 69,
                'grade': 'C',
            }), (0, 0, {
                'name': 'F',
                'marks_range_from': 0,
                'marks_range_to': 59,
                'grade': 'F',
            })],
        })
        
        # Create result template
        cls.result_template = cls.env['op.result.template'].create({
            'name': 'Standard Result Template',
            'grade_configuration_id': cls.grade_config.id,
        })
        
        # Helper methods
        cls.today = datetime.now().date()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

    def create_exam(self, **kwargs):
        """Helper method to create exam."""
        default_start = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9))
        default_end = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12))
        
        vals = {
            'name': 'Test Exam',
            'exam_code': 'TE001',
            'session_id': self.exam_session.id,
            'subject_id': self.subject1.id,
            'start_time': default_start,
            'end_time': default_end,
            'total_marks': 100,
            'min_marks': 40,
        }
        vals.update(kwargs)
        return self.env['op.exam'].create(vals)

    def create_exam_attendee(self, exam, student, **kwargs):
        """Helper method to create exam attendee."""
        vals = {
            'exam_id': exam.id,
            'student_id': student.id,
            'status': 'present',
        }
        vals.update(kwargs)
        return self.env['op.exam.attendees'].create(vals)

    def create_marksheet_register(self, **kwargs):
        """Helper method to create marksheet register."""
        vals = {
            'name': 'Test Marksheet Register',
            'exam_session_id': self.exam_session.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'grade_configuration_id': self.grade_config.id,
        }
        vals.update(kwargs)
        return self.env['op.marksheet.register'].create(vals)

    def assert_exam_state(self, exam, expected_state):
        """Helper method to assert exam state."""
        self.assertEqual(exam.state, expected_state,
                        f"Expected exam state: {expected_state}, "
                        f"actual: {exam.state}")
