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
from .test_admission_common import TestAdmissionCommon

_logger = logging.getLogger(__name__)


class TestAdmissionCompute(TestAdmissionCommon):
    """Test compute methods for admission statistics and counts."""

    def test_admission_course_computation(self):
        """Test course computation based on register settings."""
        _logger.info('Testing admission course computation')
        
        admission = self.create_test_admission()
        
        # Test course-based admission
        self.admission_register.admission_base = 'course'
        admission._compute_course_ids()
        
        # Verify course computation
        self.assertIn(self.course.id, admission.course_ids.ids)
        self.assertEqual(admission.course_id, self.course)
        
        # Test program-based admission if supported
        if hasattr(self.admission_register, 'program_id'):
            # Create program
            program = self.env['op.program'].create({
                'name': 'Test Program',
                'code': 'TP001',
            })
            
            self.admission_register.admission_base = 'program'
            self.admission_register.program_id = program.id
            
            # Create course for program
            program_course = self.op_course.create({
                'name': 'Program Course',
                'code': 'PC001',
                'evaluation_type': 'normal',
            })
            
            # Create admission fees line
            fees_line = self.env['op.admission.fees.line'].create({
                'register_id': self.admission_register.id,
                'course_id': program_course.id,
                'amount': 1500.0,
            })
            
            admission._compute_course_ids()
            
            # Verify program-based course computation
            self.assertIn(program_course.id, admission.course_ids.ids)
            
    def test_register_application_counts(self):
        """Test application count computations for register."""
        _logger.info('Testing register application counts')
        
        register = self.admission_register
        
        # Create admissions with different states
        admission_states = {
            'draft': 3,
            'submit': 5,
            'confirm': 2,
            'admission': 4,
            'done': 6,
            'reject': 1,
            'pending': 2,
            'cancel': 1,
        }
        
        created_admissions = []
        for state, count in admission_states.items():
            for i in range(count):
                admission = self.create_test_admission({
                    'email': f'{state}{i}@test.com',
                    'state': state,
                    'register_id': register.id,
                })
                created_admissions.append(admission)
                
        # Force compute
        register._compute_calculate_record_application()
        register._compute_counts()
        
        # Verify total application count
        expected_total = sum(admission_states.values())
        self.assertEqual(register.application_count, expected_total)
        
        # Verify specific state counts
        self.assertEqual(register.draft_count, admission_states['draft'])
        self.assertEqual(register.confirm_count, admission_states['confirm'])
        self.assertEqual(register.done_count, admission_states['done'])
        
    def test_register_online_application_counts(self):
        """Test online application counting."""
        _logger.info('Testing online application counts')
        
        register = self.admission_register
        
        # Create online applications (assuming online flag exists)
        online_count = 7
        offline_count = 3
        
        for i in range(online_count):
            admission = self.create_test_admission({
                'email': f'online{i}@test.com',
                'register_id': register.id,
            })
            # Mark as online if field exists
            if hasattr(admission, 'is_online'):
                admission.is_online = True
                
        for i in range(offline_count):
            admission = self.create_test_admission({
                'email': f'offline{i}@test.com',
                'register_id': register.id,
            })
            if hasattr(admission, 'is_online'):
                admission.is_online = False
                
        # Test online count computation
        if hasattr(register, '_compute_application_counts'):
            register._compute_application_counts()
            
        # Verify total applications
        total_expected = online_count + offline_count
        self.assertEqual(register.application_count, total_expected)
        
    def test_admission_name_computation(self):
        """Test name computation from first, middle, last names."""
        _logger.info('Testing admission name computation')
        
        admission = self.create_test_admission()
        
        # Test full name computation
        admission.first_name = 'John'
        admission.middle_name = 'Michael'
        admission.last_name = 'Doe'
        admission._onchange_name()
        
        self.assertEqual(admission.name, 'John Michael Doe')
        
        # Test name without middle name
        admission.middle_name = False
        admission._onchange_name()
        
        self.assertEqual(admission.name, 'John Doe')
        
        # Test name with empty middle name
        admission.middle_name = ''
        admission._onchange_name()
        
        self.assertEqual(admission.name, 'John Doe')
        
        # Test with None values
        admission.first_name = None
        admission._onchange_name()
        
        # Should handle None gracefully
        self.assertIsNotNone(admission.name)
        
    def test_admission_batch_domain_computation(self):
        """Test batch domain computation based on course."""
        _logger.info('Testing batch domain computation')
        
        # Create additional course and batch
        course2 = self.op_course.create({
            'name': 'Another Course',
            'code': 'AC001',
            'evaluation_type': 'normal',
        })
        
        batch2 = self.op_batch.create({
            'name': 'Another Batch',
            'code': 'AB001',
            'course_id': course2.id,
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(years=1),
        })
        
        admission = self.create_test_admission()
        
        # Test domain computation on course change
        admission.course_id = course2.id
        admission.onchange_course()
        
        # Verify batch filtering (if implemented)
        if hasattr(admission, 'batch_domain'):
            domain = admission.batch_domain
            # Should filter batches by course
            self.assertIn(('course_id', '=', course2.id), domain)
            
    def test_fees_computation(self):
        """Test fees computation based on register and course."""
        _logger.info('Testing fees computation')
        
        admission = self.create_test_admission()
        
        # Test fees computation from register
        if hasattr(admission, 'compute_fees'):
            admission.compute_fees()
            
        # Test fees from product if set in register
        if self.admission_register.product_id:
            expected_fees = self.admission_register.product_id.list_price
            # Fees might be computed based on product price
            
        # Test discount application
        admission.discount = 10.0  # 10% discount
        if hasattr(admission, 'compute_final_fees'):
            admission.compute_final_fees()
            
    def test_age_computation(self):
        """Test age computation from birth date."""
        _logger.info('Testing age computation')
        
        admission = self.create_test_admission()
        
        # Set specific birth date
        admission.birth_date = date.today() - relativedelta(years=20, months=6)
        
        # Test age computation if field exists
        if hasattr(admission, 'age') or hasattr(admission, 'compute_age'):
            if hasattr(admission, 'compute_age'):
                admission.compute_age()
                
            # Age should be computed correctly
            if hasattr(admission, 'age'):
                self.assertEqual(admission.age, 20)
                
    def test_application_number_computation(self):
        """Test application number generation."""
        _logger.info('Testing application number computation')
        
        # Create multiple admissions to test sequence
        admissions = []
        for i in range(5):
            admission = self.create_test_admission({
                'email': f'seq{i}@test.com'
            })
            admissions.append(admission)
            
        # Verify unique application numbers
        app_numbers = [a.application_number for a in admissions]
        unique_numbers = set(app_numbers)
        
        self.assertEqual(len(app_numbers), len(unique_numbers))
        
        # Verify format if follows pattern
        for app_num in app_numbers:
            self.assertTrue(app_num)  # Should not be empty
            
    def test_register_capacity_computation(self):
        """Test register capacity and availability computation."""
        _logger.info('Testing register capacity computation')
        
        register = self.admission_register
        register.max_count = 20
        
        # Create admissions up to capacity
        for i in range(15):
            self.create_test_admission({
                'email': f'capacity{i}@test.com',
                'register_id': register.id,
            })
            
        # Test capacity computation
        if hasattr(register, 'available_seats'):
            register._compute_available_seats()
            self.assertEqual(register.available_seats, 5)
            
        if hasattr(register, 'capacity_percentage'):
            register._compute_capacity_percentage()
            self.assertEqual(register.capacity_percentage, 75.0)
            
    def test_admission_statistics(self):
        """Test admission statistics computation."""
        _logger.info('Testing admission statistics')
        
        register = self.admission_register
        
        # Create admissions with known pattern
        male_count = 6
        female_count = 4
        
        for i in range(male_count):
            self.create_test_admission({
                'email': f'male{i}@test.com',
                'gender': 'm',
                'register_id': register.id,
            })
            
        for i in range(female_count):
            self.create_test_admission({
                'email': f'female{i}@test.com',
                'gender': 'f',
                'register_id': register.id,
            })
            
        # Test gender statistics
        if hasattr(register, '_compute_gender_stats'):
            register._compute_gender_stats()
            
            if hasattr(register, 'male_count'):
                self.assertEqual(register.male_count, male_count)
            if hasattr(register, 'female_count'):
                self.assertEqual(register.female_count, female_count)
                
    def test_admission_dependency_updates(self):
        """Test compute method dependencies and updates."""
        _logger.info('Testing compute method dependencies')
        
        admission = self.create_test_admission()
        
        # Test register change triggers computation
        new_register = self.op_register.create({
            'name': 'New Register for Dependency Test',
            'start_date': date.today(),
            'end_date': date.today() + relativedelta(months=2),
            'course_id': self.course.id,
            'academic_years_id': self.academic_year.id,
        })
        
        # Change register and verify dependencies
        admission.register_id = new_register.id
        admission._compute_course_ids()
        
        # Verify course computation updated
        self.assertIn(new_register.course_id.id, admission.course_ids.ids)
        
    def test_compute_performance(self):
        """Test performance of compute methods with bulk data."""
        _logger.info('Testing compute method performance')
        
        register = self.admission_register
        
        # Create larger dataset
        bulk_admissions = []
        for i in range(50):
            admission = self.create_test_admission({
                'email': f'bulk{i}@test.com',
                'register_id': register.id,
            })
            bulk_admissions.append(admission)
            
        # Test bulk computation performance
        import time
        
        start_time = time.time()
        register._compute_calculate_record_application()
        register._compute_counts()
        end_time = time.time()
        
        # Performance should be reasonable (less than 5 seconds for 50 records)
        computation_time = end_time - start_time
        self.assertLess(computation_time, 5.0)
        
        # Verify accuracy with bulk data
        self.assertEqual(register.application_count, 50)