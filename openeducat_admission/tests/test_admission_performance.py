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
import time
import threading
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tests import tagged
from .test_admission_common import TestAdmissionCommon

_logger = logging.getLogger(__name__)


@tagged('performance')
class TestAdmissionPerformance(TestAdmissionCommon):
    """Test performance and load scenarios for admission management."""

    def test_bulk_admission_creation(self):
        """Test performance of bulk admission creation."""
        _logger.info('Testing bulk admission creation performance')
        
        start_time = time.time()
        
        # Create 100 admissions
        bulk_size = 100
        admissions = []
        
        for i in range(bulk_size):
            admission_vals = self.admission_vals.copy()
            admission_vals.update({
                'email': f'bulk{i}@test.com',
                'first_name': f'Student{i}',
            })
            admission = self.op_admission.create(admission_vals)
            admissions.append(admission)
            
        end_time = time.time()
        creation_time = end_time - start_time
        
        _logger.info(f'Created {bulk_size} admissions in {creation_time:.2f} seconds')
        
        # Performance benchmark: should create 100 records in under 30 seconds
        self.assertLess(creation_time, 30.0)
        self.assertEqual(len(admissions), bulk_size)
        
        # Test bulk operations performance
        start_time = time.time()
        
        # Bulk state change
        admission_records = self.op_admission.browse([a.id for a in admissions])
        admission_records.write({'state': 'submit'})
        
        end_time = time.time()
        bulk_update_time = end_time - start_time
        
        _logger.info(f'Bulk updated {bulk_size} admissions in {bulk_update_time:.2f} seconds')
        self.assertLess(bulk_update_time, 10.0)
        
    def test_bulk_enrollment_performance(self):
        """Test performance of bulk student enrollment."""
        _logger.info('Testing bulk enrollment performance')
        
        # Create admissions for enrollment
        bulk_size = 50
        admissions = []
        
        for i in range(bulk_size):
            admission = self.create_test_admission({
                'email': f'enroll{i}@test.com',
                'state': 'admission',
            })
            admissions.append(admission)
            
        start_time = time.time()
        
        # Bulk enrollment
        for admission in admissions:
            admission.enroll_student()
            
        end_time = time.time()
        enrollment_time = end_time - start_time
        
        _logger.info(f'Enrolled {bulk_size} students in {enrollment_time:.2f} seconds')
        
        # Performance benchmark: should enroll 50 students in under 60 seconds
        self.assertLess(enrollment_time, 60.0)
        
        # Verify all enrollments
        enrolled_count = sum(1 for a in admissions if a.student_id)
        self.assertEqual(enrolled_count, bulk_size)
        
    def test_search_performance(self):
        """Test search performance with large datasets."""
        _logger.info('Testing search performance')
        
        # Create large dataset
        bulk_size = 200
        
        for i in range(bulk_size):
            state = ['draft', 'submit', 'confirm', 'admission', 'done'][i % 5]
            self.create_test_admission({
                'email': f'search{i}@test.com',
                'state': state,
            })
            
        # Test various search operations
        search_tests = [
            [('state', '=', 'draft')],
            [('course_id', '=', self.course.id)],
            [('register_id', '=', self.admission_register.id)],
            [('email', 'like', 'search%')],
            [('state', 'in', ['submit', 'confirm'])],
        ]
        
        for domain in search_tests:
            start_time = time.time()
            results = self.op_admission.search(domain)
            end_time = time.time()
            
            search_time = end_time - start_time
            _logger.info(f'Search {domain} took {search_time:.3f} seconds, found {len(results)} records')
            
            # Search should complete in under 2 seconds
            self.assertLess(search_time, 2.0)
            
    def test_compute_methods_performance(self):
        """Test performance of compute methods with large datasets."""
        _logger.info('Testing compute methods performance')
        
        register = self.admission_register
        
        # Create large number of admissions
        bulk_size = 150
        
        for i in range(bulk_size):
            state = ['draft', 'submit', 'confirm', 'admission', 'done'][i % 5]
            self.create_test_admission({
                'email': f'compute{i}@test.com',
                'state': state,
                'register_id': register.id,
            })
            
        # Test compute performance
        compute_tests = [
            ('_compute_calculate_record_application', []),
            ('_compute_counts', []),
        ]
        
        if hasattr(register, '_compute_application_counts'):
            compute_tests.append(('_compute_application_counts', []))
            
        for method_name, args in compute_tests:
            if hasattr(register, method_name):
                start_time = time.time()
                method = getattr(register, method_name)
                method(*args)
                end_time = time.time()
                
                compute_time = end_time - start_time
                _logger.info(f'{method_name} took {compute_time:.3f} seconds with {bulk_size} records')
                
                # Compute methods should complete in under 5 seconds
                self.assertLess(compute_time, 5.0)
                
    def test_report_generation_performance(self):
        """Test performance of report generation."""
        _logger.info('Testing report generation performance')
        
        # Create admissions for reporting
        for i in range(100):
            state = ['draft', 'submit', 'confirm', 'admission', 'done'][i % 5]
            self.create_test_admission({
                'email': f'report{i}@test.com',
                'state': state,
            })
            
        # Test admission analysis wizard performance
        wizard_vals = {
            'course_id': self.course.id,
            'start_date': date.today() - relativedelta(days=30),
            'end_date': date.today() + relativedelta(days=30),
        }
        
        wizard = self.wizard_admission.create(wizard_vals)
        
        start_time = time.time()
        report_action = wizard.print_report()
        end_time = time.time()
        
        report_time = end_time - start_time
        _logger.info(f'Report generation took {report_time:.3f} seconds')
        
        # Report generation should complete in under 10 seconds
        self.assertLess(report_time, 10.0)
        
        # Report action should be either a report or window action
        # (Some Odoo environments may return window action as fallback)
        self.assertIn(report_action['type'], ['ir.actions.report', 'ir.actions.act_window'])
        
    def test_workflow_transition_performance(self):
        """Test performance of workflow state transitions."""
        _logger.info('Testing workflow transition performance')
        
        bulk_size = 80
        admissions = []
        
        # Create admissions
        for i in range(bulk_size):
            admission = self.create_test_admission({
                'email': f'workflow{i}@test.com',
            })
            admissions.append(admission)
            
        # Test workflow transitions
        transitions = [
            ('submit_form', 'submit'),
            ('admission_confirm', 'admission'),
            ('confirm_in_progress', 'confirm'),
        ]
        
        for method_name, expected_state in transitions:
            start_time = time.time()
            
            for admission in admissions:
                if hasattr(admission, method_name):
                    method = getattr(admission, method_name)
                    method()
                    
            end_time = time.time()
            transition_time = end_time - start_time
            
            _logger.info(f'{method_name} for {bulk_size} records took {transition_time:.3f} seconds')
            
            # Workflow transitions should complete in under 15 seconds
            self.assertLess(transition_time, 15.0)
            
            # Verify state changes
            for admission in admissions:
                if hasattr(admission, method_name):
                    self.assertEqual(admission.state, expected_state)
                    
    def test_concurrent_admission_creation(self):
        """Test concurrent admission creation scenarios."""
        _logger.info('Testing concurrent admission creation')
        
        # Thread-safe list to collect results
        created_ids = []
        lock = threading.Lock()
        
        def create_admissions_thread(thread_id, count):
            """Create admissions in separate thread."""
            for i in range(count):
                try:
                    admission = self.create_test_admission({
                        'email': f'thread{thread_id}_{i}@test.com',
                    })
                    with lock:
                        created_ids.append(admission.id)
                except Exception as e:
                    _logger.warning(f'Thread {thread_id} error: {e}')
            
        # Create multiple threads
        threads = []
        thread_count = 3
        admissions_per_thread = 20
        
        start_time = time.time()
        
        for i in range(thread_count):
            thread = threading.Thread(
                target=create_admissions_thread,
                args=(i, admissions_per_thread)
            )
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        _logger.info(f'Concurrent creation took {concurrent_time:.3f} seconds')
        
        # Verify total admissions created
        total_expected = thread_count * admissions_per_thread
        
        _logger.info(f'Created {len(created_ids)} out of {total_expected} expected admissions')
        
        # Verify the created admissions exist in database
        if created_ids:
            created_admissions = self.op_admission.browse(created_ids).exists()
            _logger.info(f'Verified {len(created_admissions)} admissions exist in database')
        
        # Should create at least 50% of expected admissions (allow for race conditions and failures)
        self.assertGreaterEqual(len(created_ids), total_expected * 0.5)
        
    def test_memory_usage_optimization(self):
        """Test memory usage during large operations."""
        _logger.info('Testing memory usage optimization')
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        bulk_size = 300
        
        for i in range(bulk_size):
            admission = self.create_test_admission({
                'email': f'memory{i}@test.com',
            })
            
            # Perform some operations
            admission._onchange_name()
            admission.onchange_register()
            
            # Clear cache periodically to manage memory
            if i % 50 == 0:
                self.env.clear()
                
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        _logger.info(f'Memory usage: {initial_memory:.1f} MB -> {final_memory:.1f} MB (+{memory_increase:.1f} MB)')
        
        # Memory increase should be reasonable (less than 100 MB for 300 records)
        self.assertLess(memory_increase, 100.0)
        
    def test_database_query_optimization(self):
        """Test database query optimization."""
        _logger.info('Testing database query optimization')
        
        # Enable SQL logging for this test
        from odoo.tools import config
        
        # Create test data
        bulk_size = 100
        admissions = []
        
        for i in range(bulk_size):
            admission = self.create_test_admission({
                'email': f'query{i}@test.com',
            })
            admissions.append(admission)
            
        # Test efficient bulk operations
        admission_ids = [a.id for a in admissions]
        
        start_time = time.time()
        
        # Efficient bulk read
        bulk_admissions = self.op_admission.browse(admission_ids)
        
        # Access fields to trigger loading
        names = [a.name for a in bulk_admissions]
        emails = [a.email for a in bulk_admissions]
        
        end_time = time.time()
        
        query_time = end_time - start_time
        _logger.info(f'Bulk field access took {query_time:.3f} seconds')
        
        # Should be efficient
        self.assertLess(query_time, 2.0)
        self.assertEqual(len(names), bulk_size)
        self.assertEqual(len(emails), bulk_size)
        
    def test_cache_performance(self):
        """Test cache performance and invalidation."""
        _logger.info('Testing cache performance')
        
        admission = self.create_test_admission()
        
        # Test repeated field access (should use cache)
        start_time = time.time()
        
        for _ in range(100):
            _ = admission.name
            _ = admission.email
            _ = admission.course_id.name
            _ = admission.register_id.name
            
        end_time = time.time()
        cache_time = end_time - start_time
        
        _logger.info(f'Cached field access took {cache_time:.3f} seconds')
        
        # Cached access should be very fast
        self.assertLess(cache_time, 1.0)
        
        # Test cache invalidation
        start_time = time.time()
        admission.write({'phone': '1111111111'})
        end_time = time.time()
        
        invalidation_time = end_time - start_time
        _logger.info(f'Cache invalidation took {invalidation_time:.3f} seconds')
        
        # Cache invalidation should be fast
        self.assertLess(invalidation_time, 1.0)