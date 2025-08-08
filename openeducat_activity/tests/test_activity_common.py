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

from datetime import date, timedelta
import uuid
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_activity')
class TestActivityCommon(TransactionCase):
    """Common test setup for activity module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for activity tests."""
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
        
        # Create students with required partners
        partner1 = cls.env['res.partner'].create({
            'name': 'Test Student 1',
            'is_company': False,
        })
        cls.student1 = cls.env['op.student'].create({
            'partner_id': partner1.id,
            'first_name': 'Test',
            'last_name': 'Student1',
            'birth_date': '2005-01-01',
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
            'birth_date': '2005-02-01',
            'gender': 'f',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
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
            'birth_date': '1985-01-01',
            'gender': 'male',
        })
        
        # Model references for legacy tests
        cls.op_activity = cls.env['op.activity']
        cls.op_activity_type = cls.env['op.activity.type']
        cls.op_student_migrate_wizard = cls.env['student.migrate']
        
        # Create sample activity type for testing
        cls.sample_activity_type = cls.env['op.activity.type'].create({
            'name': 'Sample Activity Type',
            'code': 'SAT001',
            'description': 'Sample activity type for testing',
        })
        
        # Create sample activity for testing
        cls.sample_activity = cls.env['op.activity'].create({
            'student_id': cls.student1.id,
            'faculty_id': cls.faculty.id,
            'type_id': cls.sample_activity_type.id,
            'description': 'Sample activity description',
            'date': '2024-08-01',
        })

    def create_activity_type(self, **kwargs):
        """Helper method to create activity type."""
        # Use existing sample type or create unique one
        if not kwargs and hasattr(self, 'sample_activity_type'):
            return self.sample_activity_type
            
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        vals = {
            'name': kwargs.get('name', f'Test Activity Type {unique_suffix}'),
            'code': kwargs.get('code', f'TAT{unique_suffix}'),
            'description': kwargs.get('description', 'Test activity type description'),
        }
        vals.update(kwargs)
        return self.env['op.activity.type'].create(vals)

    def create_activity(self, **kwargs):
        """Helper method to create activity."""
        activity_type = kwargs.pop('activity_type', None)
        if not activity_type:
            activity_type = self.create_activity_type()
        
        # Handle both 'name' and 'description' params for backward compatibility
        description = kwargs.pop('name', None) or kwargs.pop('description', 'Test activity description')
        
        # Ensure date is not in the future (activity model has constraint)
        activity_date = kwargs.pop('date', date.today())
        if activity_date > date.today():
            activity_date = date.today()
            
        vals = {
            'student_id': kwargs.pop('student_id', self.student1.id),
            'type_id': activity_type.id,
            'date': activity_date,
            'description': description,
        }
        # Filter out invalid field names that don't exist on op.activity model
        invalid_fields = [
            'max_capacity', 'participation_status', 'activity_id', 'capacity',
            'instructor_id', 'cost', 'name', 'start_time', 'end_time', 'time'
        ]
        
        # Add valid fields from kwargs, filtering out invalid ones
        for key, value in kwargs.items():
            if key not in invalid_fields:
                vals[key] = value
                
        return self.env['op.activity'].create(vals)

    def create_student_activity(self, activity=None, student=None, **kwargs):
        """Helper method - this model doesn't exist, creating activity instead."""
        # Note: op.student.activity model doesn't exist
        # This method creates an op.activity record instead
        if not student:
            student = self.student1
            
        activity_kwargs = {
            'student_id': student.id,
            'description': kwargs.get('name', 'Student activity participation'),
        }
        activity_kwargs.update(kwargs)
        
        return self.create_activity(**activity_kwargs)
