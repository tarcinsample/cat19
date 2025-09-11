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
        
        # Create exam session with all required fields
        cls.exam_session = cls.env['op.exam.session'].create({
            'name': 'Test Exam Session',
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'exam_code': 'TES2024',
            'start_date': '2024-11-01',
            'end_date': '2024-11-30',
            'exam_type': cls.exam_type.id,
            'evaluation_type': 'normal',
            'state': 'schedule',
        })
        
        # Create grade configuration with correct fields
        cls.grade_config = cls.env['op.grade.configuration'].create({
            'min_per': 90,
            'max_per': 100, 
            'result': 'A+',
        })
        
        # Create result template with correct fields
        cls.result_template = cls.env['op.result.template'].create({
            'name': 'Standard Result Template',
            'exam_session_id': cls.exam_session.id,
            'result_date': '2024-11-30',
            'grade_ids': [(6, 0, [cls.grade_config.id])],
        })
        
        # Model references for legacy tests
        cls.op_exam = cls.env['op.exam']
        cls.op_exam_attendees = cls.env['op.exam.attendees']
        cls.op_exam_room = cls.env['op.exam.room']
        cls.op_exam_type = cls.env['op.exam.type']
        cls.op_grade_configuration = cls.env['op.grade.configuration']
        cls.op_marksheet_line = cls.env['op.marksheet.line']
        cls.op_marksheet_register = cls.env['op.marksheet.register']
        cls.op_result_line = cls.env['op.result.line']
        cls.op_result_template = cls.env['op.result.template']
        cls.op_exam_session = cls.env['op.exam.session']
        cls.op_held_exam = cls.env['op.held.exam']
        cls.op_room_distribution = cls.env['op.room.distribution']
        
        # Helper methods
        cls.today = datetime.now().date()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

    def create_exam(self, **kwargs):
        """Helper method to create exam."""
        # Use a date within the exam session period (2024-11-01 to 2024-11-30)
        from datetime import date
        exam_date = date(2024, 11, 15)  # Within session dates
        default_start = datetime.combine(exam_date, datetime.min.time().replace(hour=9))
        default_end = datetime.combine(exam_date, datetime.min.time().replace(hour=12))
        
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
            'result_template_id': self.result_template.id,
        }
        vals.update(kwargs)
        return self.env['op.marksheet.register'].create(vals)

    def assert_exam_state(self, exam, expected_state):
        """Helper method to assert exam state."""
        self.assertEqual(exam.state, expected_state,
                        f"Expected exam state: {expected_state}, "
                        f"actual: {exam.state}")
