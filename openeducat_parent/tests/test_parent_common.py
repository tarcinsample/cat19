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

from datetime import date
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_parent')
class TestParentCommon(TransactionCase):
    """Common test setup for parent module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for parent tests."""
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
        
        # Create students
        cls.student1 = cls.env['op.student'].create({
            'name': 'Test Student 1',
            'first_name': 'Test',
            'last_name': 'Student1',
            'birth_date': '2005-01-01',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        cls.student2 = cls.env['op.student'].create({
            'name': 'Test Student 2',
            'first_name': 'Test',
            'last_name': 'Student2',
            'birth_date': '2005-02-02',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })

    def create_parent(self, **kwargs):
        """Helper method to create parent."""
        vals = {
            'name': 'Test Parent',
            'first_name': 'Test',
            'last_name': 'Parent',
            'email': 'parent@test.com',
            'phone': '+1234567890',
            'is_parent': True,
        }
        vals.update(kwargs)
        return self.env['op.parent'].create(vals)

    def create_parent_relationship(self, parent, student, relation_type='father', **kwargs):
        """Helper method to create parent-student relationship."""
        vals = {
            'parent_id': parent.id,
            'student_id': student.id,
            'relation': relation_type,
        }
        vals.update(kwargs)
        return self.env['op.parent.relation'].create(vals)
