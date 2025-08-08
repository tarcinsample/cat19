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
import uuid
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_parent')
class TestParentCommon(TransactionCase):
    """Common test setup for parent module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for parent tests."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create or get parent relationship types
        cls.relationship_father = cls.env['op.parent.relationship'].search([('name', '=', 'Father')], limit=1)
        if not cls.relationship_father:
            cls.relationship_father = cls.env['op.parent.relationship'].create({
                'name': 'Father',
                'description': 'Father relationship'
            })
        
        cls.relationship_mother = cls.env['op.parent.relationship'].search([('name', '=', 'Mother')], limit=1)
        if not cls.relationship_mother:
            cls.relationship_mother = cls.env['op.parent.relationship'].create({
                'name': 'Mother',
                'description': 'Mother relationship'
            })
        
        cls.relationship_guardian = cls.env['op.parent.relationship'].search([('name', '=', 'Guardian')], limit=1)
        if not cls.relationship_guardian:
            cls.relationship_guardian = cls.env['op.parent.relationship'].create({
                'name': 'Guardian',
                'description': 'Guardian relationship'
            })
        
        # Model references for legacy tests
        cls.op_parent = cls.env['op.parent']
        cls.op_student = cls.env['op.student']
        cls.subject_registration = cls.env['op.subject.registration']
        
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
            'birth_date': '2005-02-02',
            'gender': 'f',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })

    def create_parent(self, **kwargs):
        """Helper method to create parent."""
        # Always create partner if 'name' field is a string (not an ID)
        partner = None
        parent_name = kwargs.pop('parent_name', kwargs.pop('name', 'Test Parent'))
        
        # If parent_name is a string, create the partner
        if isinstance(parent_name, str):
            partner = self.env['res.partner'].create({
                'name': parent_name,
                'email': kwargs.pop('email', 'parent@test.com'),
                'phone': kwargs.pop('phone', '+1234567890'),
                'is_company': False,
            })
            name_field = partner.id
        else:
            name_field = parent_name  # It's already an ID
        
        vals = {
            'name': name_field,
            'relationship_id': self.relationship_father.id,
        }
        
        # Remove fields that are not valid for op.parent model
        invalid_fields = ['first_name', 'last_name', 'email', 'phone', 'is_parent', 'parent_name', 'street']
        for field in invalid_fields:
            kwargs.pop(field, None)
            
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
        # Create or get the relationship type
        relationship_type = self.env['op.parent.relationship'].search([('name', '=', relation_type.title())], limit=1)
        if not relationship_type:
            relationship_type = self.env['op.parent.relationship'].create({
                'name': relation_type.title(),
                'description': f'{relation_type.title()} relationship'
            })
        
        # Update the parent's relationship_id to match the requested relation type
        parent.write({'relationship_id': relationship_type.id})
        
        # Add the student to the parent's student_ids
        parent.write({'student_ids': [(4, student.id)]})
        
        # Also add parent to student's parent_ids if the field exists
        if hasattr(student, 'parent_ids'):
            student.write({'parent_ids': [(4, parent.id)]})
            
        return parent  # Return the parent instead of a separate relation record
