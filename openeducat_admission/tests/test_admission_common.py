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

from datetime import datetime, date
import uuid
from dateutil.relativedelta import relativedelta
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestAdmissionCommon(TransactionCase):
    """Common setup for admission tests with comprehensive test data."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
    def setUp(self):
        super(TestAdmissionCommon, self).setUp()
        self.op_register = self.env['op.admission.register']
        self.op_admission = self.env['op.admission']
        self.wizard_admission = self.env['admission.analysis']
        self.op_student = self.env['op.student']
        self.op_course = self.env['op.course']
        self.op_batch = self.env['op.batch']
        self.op_academic_year = self.env['op.academic.year']
        self.op_academic_term = self.env['op.academic.term']
        self.op_fees_terms = self.env['op.fees.terms']
        self.res_partner = self.env['res.partner']
        
        # Create test academic year
        self.academic_year = self.op_academic_year.create({
            'name': 'Test Academic Year 2024-25',
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(years=1),
        })
        
        # Create test academic term
        self.academic_term = self.op_academic_term.create({
            'name': 'Test Term 1',
            'academic_year_id': self.academic_year.id,
            'term_start_date': date.today(),
            'term_end_date': date.today() + relativedelta(months=6),
        })
        
        # Create test course
        self.course = self.op_course.create({
            'name': 'Test Course for Admission',
            'code': 'TCA001',
            'evaluation_type': 'normal',
        })
        
        # Create test batch
        self.batch = self.op_batch.create({
            'name': 'Test Batch 2024',
            'code': 'TB2024_' + str(uuid.uuid4())[:8].replace('-', ''),
            'course_id': self.course.id,
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(years=1),
        })
        
        # Create test product for fees
        self.fees_product = self.env['product.product'].create({
            'name': 'Admission Fee Product',
            'type': 'service',
            'list_price': 1000.0,
        })
        
        # Create test fees terms
        self.fees_term = self.op_fees_terms.create({
            'name': 'Test Admission Fees',
            'code': 'TAF001',
            'fees_terms': 'fixed_days',
            'no_days': 30,
            'day_type': 'after',
        })
        
        # Create test admission register
        self.admission_register = self.op_register.create({
            'name': 'Test Admission Register 2024',
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(months=3),
            'course_id': self.course.id,
            'academic_years_id': self.academic_year.id,
            'academic_term_id': self.academic_term.id,
            'min_count': 5,
            'max_count': 50,
            'minimum_age_criteria': 18,
            'product_id': self.fees_product.id,
            'admission_base': 'course',
        })
        
        # Test admission data
        self.admission_vals = {
            'name': 'Test Student Name',
            'first_name': 'Test',
            'middle_name': 'Middle',
            'last_name': 'Student',
            'birth_date': date.today() - relativedelta(years=20),
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'phone': '1234567890',
            'mobile': '9876543210',
            'email': 'test.student@example.com',
            'gender': 'm',
            'register_id': self.admission_register.id,
            'fees': 1000.0,
            'fees_term_id': self.fees_term.id,
            'fees_start_date': date.today(),
            'application_date': datetime.now(),
            'company_id': self.env.user.company_id.id,
        }
        
    def create_test_admission(self, vals=None):
        """Helper method to create test admission with default or custom values."""
        admission_vals = self.admission_vals.copy()
        if vals:
            admission_vals.update(vals)
        return self.op_admission.create(admission_vals)
        
    def create_multiple_admissions(self, count=5, state_distribution=None):
        """Create multiple test admissions with different states."""
        admissions = self.env['op.admission']
        states = state_distribution or ['draft', 'submit', 'confirm', 'admission', 'done']
        
        for i in range(count):
            state = states[i % len(states)]
            vals = {
                'email': f'student{i}@example.com',
                'first_name': f'Student{i}',
                'state': state,
            }
            admission = self.create_test_admission(vals)
            admissions += admission
            
        return admissions