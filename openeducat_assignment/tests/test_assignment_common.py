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
from odoo.tests import TransactionCase


class TestAssignmentCommon(TransactionCase):
    """Common test setup for assignment module tests."""
    
    def setUp(self):
        super(TestAssignmentCommon, self).setUp()
        
        # Model references
        self.op_assignment = self.env['op.assignment']
        self.op_assignment_subline = self.env['op.assignment.sub.line']
        self.op_assignment_type = self.env['grading.assignment.type']
        self.grading_assignment = self.env['grading.assignment']
        self.op_student = self.env['op.student']
        self.op_faculty = self.env['op.faculty']
        self.op_course = self.env['op.course']
        self.op_batch = self.env['op.batch']
        self.op_subject = self.env['op.subject']
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create comprehensive test data for assignment tests."""
        
        # Create assignment type
        self.assignment_type = self.op_assignment_type.create({
            'name': 'Test Assignment Type',
            'code': 'TEST',
            'assign_type': 'sub'
        })
        
        # Get or create test course
        self.course = self.env.ref('openeducat_core.op_course_1', raise_if_not_found=False)
        if not self.course:
            self.course = self.op_course.create({
                'name': 'Test Course',
                'code': 'TC001'
            })
        
        # Get or create test batch
        self.batch = self.env.ref('openeducat_core.op_batch_1', raise_if_not_found=False)
        if not self.batch:
            from datetime import date
            self.batch = self.op_batch.create({
                'name': 'Test Batch',
                'code': 'TB001_' + str(uuid.uuid4())[:8].replace('-', ''),
                'course_id': self.course.id,
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=365)
            })
        
        # Get or create test subject
        self.subject = self.env.ref('openeducat_core.op_subject_1', raise_if_not_found=False)
        if not self.subject:
            self.subject = self.op_subject.create({
                'name': 'Test Subject',
                'code': 'TS001'
            })
        
        # Get or create test faculty
        self.faculty = self.env.ref('openeducat_core.op_faculty_1', raise_if_not_found=False)
        if not self.faculty:
            # Create partner for faculty
            faculty_partner = self.env['res.partner'].create({
                'name': 'Test Faculty',
                'is_company': False
            })
            self.faculty = self.op_faculty.create({
                'partner_id': faculty_partner.id,
                'first_name': 'Test',
                'last_name': 'Faculty',
                'birth_date': '1980-01-01',
                'gender': 'male'
            })
        
        # Get or create test students
        self.student1 = self.env.ref('openeducat_core.op_student_1', raise_if_not_found=False)
        if not self.student1:
            student1_partner = self.env['res.partner'].create({
                'name': 'Test Student 1',
                'is_company': False
            })
            self.student1 = self.op_student.create({
                'partner_id': student1_partner.id,
                'first_name': 'Test',
                'last_name': 'Student1',
                'birth_date': '2000-01-01',
                'gender': 'm'
            })
        
        self.student2 = self.env.ref('openeducat_core.op_student_2', raise_if_not_found=False)
        if not self.student2:
            student2_partner = self.env['res.partner'].create({
                'name': 'Test Student 2',
                'is_company': False
            })
            self.student2 = self.op_student.create({
                'partner_id': student2_partner.id,
                'first_name': 'Test',
                'last_name': 'Student2',
                'birth_date': '2000-01-01',
                'gender': 'm'
            })
        
        # Create grading assignment with all required fields
        self.grading_assignment_obj = self.grading_assignment.create({
            'name': 'Test Grading Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=30),  # Add end_date field
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        # Base assignment data
        self.assignment_data = {
            'grading_assignment_id': self.grading_assignment_obj.id,
            'batch_id': self.batch.id,
            'marks': 100,
            'description': 'Test assignment description',
            'state': 'draft',
            'submission_date': datetime.now() + timedelta(days=7),
            'allocation_ids': [(6, 0, [self.student1.id, self.student2.id])]
        }
        
        # Grading assignment data template (for other tests to use)
        self.grading_assignment_data = {
            'name': 'Test Grading Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=30),  # Add end_date field
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        }
        
        # Assignment submission data
        self.submission_data = {
            'student_id': self.student1.id,
            'description': 'Test submission description',
            'state': 'draft',
            'submission_date': datetime.now()  # Ensure submission_date is provided
        }
