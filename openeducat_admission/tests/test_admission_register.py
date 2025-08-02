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

import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from .test_admission_common import TestAdmissionCommon

_logger = logging.getLogger(__name__)


class TestAdmissionRegister(TestAdmissionCommon):
    """Test admission register management and session handling."""

    def test_register_create_basic(self):
        """Test basic admission register creation."""
        _logger.info('Testing basic admission register creation')
        
        register = self.op_register.create({
            'name': 'Test Register 2024',
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(months=2),
            'course_id': self.course.id,
            'academic_years_id': self.academic_year.id,
            'min_count': 10,
            'max_count': 100,
        })
        
        # Verify register creation
        self.assertTrue(register.id)
        self.assertEqual(register.state, 'draft')
        self.assertEqual(register.name, 'Test Register 2024')
        self.assertEqual(register.course_id, self.course)
        self.assertEqual(register.min_count, 10)
        self.assertEqual(register.max_count, 100)
        
    def test_register_workflow_states(self):
        """Test admission register workflow state transitions."""
        _logger.info('Testing admission register workflow states')
        
        register = self.admission_register
        
        # Test draft -> confirm
        self.assertEqual(register.state, 'draft')
        register.confirm_register()
        self.assertEqual(register.state, 'confirm')
        
        # Test confirm -> application
        register.start_application()
        self.assertEqual(register.state, 'application')
        
        # Test application -> admission
        register.start_admission()
        self.assertEqual(register.state, 'admission')
        
        # Test admission -> done
        register.close_register()
        self.assertEqual(register.state, 'done')
        
        # Test back to draft
        register.set_to_draft()
        self.assertEqual(register.state, 'draft')
        
        # Test cancel workflow
        register.cancel_register()
        self.assertEqual(register.state, 'cancel')
        
    def test_register_validation_methods(self):
        """Test admission register validation methods."""
        _logger.info('Testing admission register validation methods')
        
        register = self.admission_register
        
        # Test date validation
        register.check_dates()
        
        # Test invalid date range
        with self.assertRaises((ValidationError, UserError)):
            register.write({
                'start_date': date.today() + relativedelta(days=10),
                'end_date': date.today(),  # End date before start date
            })
            register.check_dates()
            
        # Test admission count validation
        register.check_no_of_admission()
        
        # Create admissions and test count validation
        admissions = []
        for i in range(register.max_count + 5):  # Exceed max count
            try:
                admission = self.create_test_admission({
                    'email': f'student{i}@test.com',
                    'register_id': register.id,
                })
                admissions.append(admission)
            except (ValidationError, UserError):
                break  # Expected when max count is reached
                
        # Verify max count validation
        if len(admissions) > register.max_count:
            with self.assertRaises((ValidationError, UserError)):
                register.check_no_of_admission()
                
    def test_register_compute_methods(self):
        """Test computed fields for admission register."""
        _logger.info('Testing admission register compute methods')
        
        register = self.admission_register
        
        # Create test admissions with different states
        admissions_data = [
            {'email': 'draft1@test.com', 'state': 'draft'},
            {'email': 'draft2@test.com', 'state': 'draft'},
            {'email': 'submit1@test.com', 'state': 'submit'},
            {'email': 'confirm1@test.com', 'state': 'confirm'},
            {'email': 'done1@test.com', 'state': 'done'},
        ]
        
        for data in admissions_data:
            self.create_test_admission({
                'email': data['email'],
                'state': data['state'],
                'register_id': register.id,
            })
            
        # Trigger compute methods
        register._compute_calculate_record_application()
        register._compute_counts()
        
        # Verify application count
        self.assertEqual(register.application_count, 5)
        
        # Verify state-specific counts
        self.assertEqual(register.draft_count, 2)
        self.assertEqual(register.confirm_count, 1)
        self.assertEqual(register.done_count, 1)
        
    def test_register_admission_base_onchange(self):
        """Test admission base onchange functionality."""
        _logger.info('Testing admission base onchange')
        
        register = self.admission_register
        
        # Test course-based admission
        register.admission_base = 'course'
        register.onchange_admission_base()
        
        # Test program-based admission
        if hasattr(register, 'program_id'):
            register.admission_base = 'program'
            register.onchange_admission_base()
            self.assertFalse(register.course_id)
            self.assertFalse(register.product_id)
            
    def test_register_course_computation(self):
        """Test course computation for admissions."""
        _logger.info('Testing register course computation')
        
        register = self.admission_register
        
        # Create admission and test course computation
        admission = self.create_test_admission({'register_id': register.id})
        admission._compute_course_ids()
        
        # Verify course computation
        if register.admission_base == 'course':
            self.assertIn(register.course_id.id, admission.course_ids.ids)
        
    def test_register_product_integration(self):
        """Test product integration for fees calculation."""
        _logger.info('Testing register product integration')
        
        # Create product for fees
        product = self.env['product.product'].create({
            'name': 'Admission Fee Product',
            'type': 'service',
            'list_price': 2000.0,
        })
        
        register = self.op_register.create({
            'name': 'Test Register with Product',
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(months=2),
            'course_id': self.course.id,
            'product_id': product.id,
            'academic_years_id': self.academic_year.id,
        })
        
        # Verify product integration
        self.assertEqual(register.product_id, product)
        
        # Create admission and verify fees
        admission = self.create_test_admission({
            'register_id': register.id,
            'email': 'product.test@example.com',
        })
        
        # Test fees calculation based on product
        if hasattr(admission, 'calculate_fees'):
            admission.calculate_fees()
            
    def test_register_academic_year_integration(self):
        """Test academic year and term integration."""
        _logger.info('Testing academic year integration')
        
        register = self.admission_register
        
        # Verify academic year integration
        self.assertEqual(register.academic_years_id, self.academic_year)
        self.assertEqual(register.academic_term_id, self.academic_term)
        
        # Test constraints with academic year
        with self.assertRaises((ValidationError, UserError)):
            self.op_register.create({
                'name': 'Invalid Register',
                'start_date': self.academic_year.date_stop + relativedelta(days=1),
                'end_date': self.academic_year.date_stop + relativedelta(days=30),
                'course_id': self.course.id,
                'academic_years_id': self.academic_year.id,
            })
            
    def test_register_minimum_age_criteria(self):
        """Test minimum age criteria validation."""
        _logger.info('Testing minimum age criteria')
        
        register = self.admission_register
        register.minimum_age_criteria = 18
        
        # Test admission with valid age
        valid_admission = self.create_test_admission({
            'birth_date': date.today() - relativedelta(years=20),
            'email': 'valid.age@test.com',
            'register_id': register.id,
        })
        valid_admission._check_birthdate()
        
        # Test admission with invalid age
        with self.assertRaises((ValidationError, UserError)):
            invalid_admission = self.create_test_admission({
                'birth_date': date.today() - relativedelta(years=16),
                'email': 'invalid.age@test.com',
                'register_id': register.id,
            })
            invalid_admission._check_birthdate()
            
    def test_register_favorite_functionality(self):
        """Test register favorite functionality."""
        _logger.info('Testing register favorite functionality')
        
        register = self.admission_register
        
        # Test marking as favorite
        register.is_favorite = True
        self.assertTrue(register.is_favorite)
        
        # Test favorite filter
        favorite_registers = self.op_register.search([('is_favorite', '=', True)])
        self.assertIn(register, favorite_registers)
        
    def test_register_company_integration(self):
        """Test multi-company integration."""
        _logger.info('Testing register company integration')
        
        register = self.admission_register
        
        # Verify company assignment
        self.assertEqual(register.company_id, self.env.company)
        
        # Test company-specific search
        company_registers = self.op_register.search([
            ('company_id', '=', self.env.company.id)
        ])
        self.assertIn(register, company_registers)
        
    def test_register_application_counting(self):
        """Test application counting methods."""
        _logger.info('Testing application counting methods')
        
        register = self.admission_register
        
        # Create diverse applications
        online_admissions = []
        offline_admissions = []
        
        for i in range(3):
            # Online applications
            online_admission = self.create_test_admission({
                'email': f'online{i}@test.com',
                'register_id': register.id,
            })
            online_admissions.append(online_admission)
            
            # Offline applications
            offline_admission = self.create_test_admission({
                'email': f'offline{i}@test.com',
                'register_id': register.id,
            })
            offline_admissions.append(offline_admission)
            
        # Test compute methods
        register._compute_application_counts()
        
        # Verify total count
        total_expected = len(online_admissions) + len(offline_admissions)
        self.assertEqual(register.application_count, total_expected)
        
    def test_register_date_constraints(self):
        """Test date-related constraints and validations."""
        _logger.info('Testing register date constraints')
        
        # Test overlapping registers for same course
        overlapping_register = self.op_register.create({
            'name': 'Overlapping Register',
            'start_date': self.admission_register.start_date + relativedelta(days=15),
            'end_date': self.admission_register.end_date + relativedelta(days=15),
            'course_id': self.course.id,
            'academic_years_id': self.academic_year.id,
        })
        
        # Both registers should be valid (overlapping might be allowed)
        self.assertTrue(overlapping_register.id)
        
        # Test past date validation
        with self.assertRaises((ValidationError, UserError)):
            self.op_register.create({
                'name': 'Past Date Register',
                'start_date': date.today() - relativedelta(months=2),
                'end_date': date.today() - relativedelta(months=1),
                'course_id': self.course.id,
                'academic_years_id': self.academic_year.id,
            })
            
    def test_register_bulk_operations(self):
        """Test bulk operations on admission registers."""
        _logger.info('Testing register bulk operations')
        
        # Create multiple registers
        registers = []
        for i in range(5):
            register = self.op_register.create({
                'name': f'Bulk Register {i}',
                'start_date': date.today() + relativedelta(days=i),
                'end_date': date.today() + relativedelta(days=i+30),
                'course_id': self.course.id,
                'academic_years_id': self.academic_year.id,
            })
            registers.append(register)
            
        # Test bulk state changes
        register_records = self.op_register.browse([r.id for r in registers])
        register_records.confirm_register()
        
        for register in register_records:
            self.assertEqual(register.state, 'confirm')
            
        # Test bulk operations
        register_records.start_application()
        for register in register_records:
            self.assertEqual(register.state, 'application')