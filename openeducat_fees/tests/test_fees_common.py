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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_fees')
class TestFeesCommon(TransactionCase):
    """Common test setup for fees module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for fees tests."""
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
        
        # Create product category for fees
        cls.fees_category = cls.env['product.category'].create({
            'name': 'Education Fees',
        })
        
        # Create fee products
        cls.tuition_product = cls.env['product.product'].create({
            'name': 'Tuition Fee',
            'type': 'service',
            'categ_id': cls.fees_category.id,
            'list_price': 1000.0,
        })
        
        cls.library_product = cls.env['product.product'].create({
            'name': 'Library Fee',
            'type': 'service',
            'categ_id': cls.fees_category.id,
            'list_price': 200.0,
        })

    def create_fees_element(self, **kwargs):
        """Helper method to create fees element."""
        vals = {
            'name': 'Test Fee Element',
            'product_id': self.tuition_product.id,
            'amount': 500.0,
        }
        vals.update(kwargs)
        return self.env['op.fees.element'].create(vals)

    def create_fees_terms(self, **kwargs):
        """Helper method to create fees terms."""
        vals = {
            'name': 'Test Fee Term',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'academic_year_id': self.academic_year.id,
            'term_start_date': '2024-06-01',
            'term_end_date': '2024-08-31',
        }
        vals.update(kwargs)
        return self.env['op.fees.terms'].create(vals)

    def create_student_fees_details(self, student=None, **kwargs):
        """Helper method to create student fees details."""
        if not student:
            student = self.student1
        
        vals = {
            'student_id': student.id,
            'fees_line_id': self.create_fees_element().id,
            'amount': 500.0,
            'state': 'draft',
        }
        vals.update(kwargs)
        return self.env['op.student.fees.details'].create(vals)
