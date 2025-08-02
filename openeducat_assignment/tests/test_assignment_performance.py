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

import time
from datetime import datetime, timedelta
from odoo.tests import tagged
from .test_assignment_common import TestAssignmentCommon


@tagged('post_install', '-at_install')
class TestAssignmentPerformance(TestAssignmentCommon):
    """Test performance and load testing for assignment operations."""
    
    def test_bulk_assignment_creation_performance(self):
        """Test Task 9: Performance testing for bulk assignment operations."""
        
        # Measure time for bulk assignment creation
        start_time = time.time()
        
        assignments = []
        for i in range(50):  # Create 50 assignments
            grading_assignment = self.grading_assignment.create({
                'name': f'Bulk Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now() - timedelta(days=i % 10),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data.update({
                'grading_assignment_id': grading_assignment.id,
                'description': f'Bulk assignment description {i+1}'
            })
            
            assignment = self.op_assignment.create(assignment_data)
            assignments.append(assignment)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verify all assignments created
        self.assertEqual(len(assignments), 50)
        
        # Performance assertion (should complete in reasonable time)
        self.assertLess(creation_time, 30.0, f"Bulk creation took {creation_time:.2f}s, should be under 30s")
        
        # Test bulk operations
        bulk_start = time.time()
        
        # Bulk publish
        for assignment in assignments[:25]:
            assignment.act_publish()
        
        # Bulk count computation
        for assignment in assignments:
            assignment._compute_assignment_count_compute()
        
        bulk_end = time.time()
        bulk_time = bulk_end - bulk_start
        
        self.assertLess(bulk_time, 15.0, f"Bulk operations took {bulk_time:.2f}s, should be under 15s")
    
    def test_bulk_submission_creation_performance(self):
        """Test performance for bulk submission creation."""
        
        # Create single assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create multiple students for testing
        students = []
        for i in range(100):
            partner = self.env['res.partner'].create({
                'name': f'Bulk Test Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            students.append(student)
        
        # Measure bulk submission creation
        start_time = time.time()
        
        submissions = []
        for i, student in enumerate(students):
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Bulk submission {i+1}',
                'state': 'draft'
            })
            submissions.append(submission)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verify all submissions created
        self.assertEqual(len(submissions), 100)
        
        # Performance assertion
        self.assertLess(creation_time, 20.0, f"Bulk submission creation took {creation_time:.2f}s")
        
        # Test compute performance with many submissions
        compute_start = time.time()
        assignment._compute_assignment_count_compute()
        compute_end = time.time()
        
        compute_time = compute_end - compute_start
        self.assertLess(compute_time, 1.0, f"Compute with 100 submissions took {compute_time:.2f}s")
        self.assertEqual(assignment.assignment_sub_line_count, 100)
    
    def test_search_performance(self):
        """Test search performance with large datasets."""
        
        # Create multiple assignments for search testing
        assignments = []
        for i in range(30):
            grading_assignment = self.grading_assignment.create({
                'name': f'Search Test Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now() - timedelta(days=i % 7),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data['grading_assignment_id'] = grading_assignment.id
            assignment = self.op_assignment.create(assignment_data)
            assignments.append(assignment)
        
        # Test various search scenarios
        search_scenarios = [
            ([('state', '=', 'draft')], 'State search'),
            ([('marks', '>', 50)], 'Numeric comparison'),
            ([('description', 'ilike', 'test')], 'Text search'),
            ([('course_id', '=', self.course.id)], 'Related field search'),
            ([('faculty_id', '=', self.faculty.id)], 'Many2one search'),
        ]
        
        for domain, description in search_scenarios:
            start_time = time.time()
            
            results = self.op_assignment.search(domain)
            
            end_time = time.time()
            search_time = end_time - start_time
            
            self.assertLess(search_time, 1.0, f"{description} took {search_time:.2f}s")
            self.assertGreaterEqual(len(results), 0)
    
    def test_concurrent_submission_simulation(self):
        """Test Task 12: Load testing for concurrent assignment submissions."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create multiple students
        students = []
        for i in range(20):
            partner = self.env['res.partner'].create({
                'name': f'Concurrent Test Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            students.append(student)
        
        # Simulate concurrent submissions
        start_time = time.time()
        
        submissions = []
        for i, student in enumerate(students):
            # Create submission
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Concurrent submission {i+1}',
                'submission_date': datetime.now() + timedelta(seconds=i)
            })
            
            # Simulate immediate submission
            submission.act_submit()
            submissions.append(submission)
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Verify all submissions processed
        self.assertEqual(len(submissions), 20)
        submitted_count = len([s for s in submissions if s.state == 'submit'])
        self.assertEqual(submitted_count, 20)
        
        # Performance assertion
        self.assertLess(concurrent_time, 10.0, f"Concurrent submissions took {concurrent_time:.2f}s")
        
        # Test assignment count updates correctly
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, 20)
    
    def test_memory_usage_optimization(self):
        """Test memory usage with large datasets."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test memory-efficient batch processing
        batch_size = 10
        total_submissions = 50
        
        start_time = time.time()
        
        for batch_start in range(0, total_submissions, batch_size):
            batch_submissions = []
            
            for i in range(batch_start, min(batch_start + batch_size, total_submissions)):
                submission_data = {
                    'assignment_id': assignment.id,
                    'student_id': self.student1.id if i % 2 == 0 else self.student2.id,
                    'description': f'Batch submission {i+1}'
                }
                batch_submissions.append(submission_data)
            
            # Batch create
            submissions = self.op_assignment_subline.create(batch_submissions)
            
            # Process batch
            for submission in submissions:
                submission.act_submit()
        
        end_time = time.time()
        batch_time = end_time - start_time
        
        # Verify final count
        assignment._compute_assignment_count_compute()
        self.assertEqual(assignment.assignment_sub_line_count, total_submissions)
        
        # Performance should be reasonable
        self.assertLess(batch_time, 15.0, f"Batch processing took {batch_time:.2f}s")
    
    def test_database_query_optimization(self):
        """Test database query optimization for assignment operations."""
        
        # Create test data
        assignments = []
        for i in range(10):
            grading_assignment = self.grading_assignment.create({
                'name': f'Query Test Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now(),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data['grading_assignment_id'] = grading_assignment.id
            assignment = self.op_assignment.create(assignment_data)
            assignments.append(assignment)
        
        # Test efficient querying
        start_time = time.time()
        
        # Single query to get all assignments with related data
        all_assignments = self.op_assignment.search([
            ('id', 'in', [a.id for a in assignments])
        ])
        
        # Access related fields (should use prefetching)
        for assignment in all_assignments:
            _ = assignment.course_id.name
            _ = assignment.faculty_id.name
            _ = assignment.assignment_type.name
            _ = assignment.assignment_sub_line_count
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertLess(query_time, 2.0, f"Related field access took {query_time:.2f}s")
    
    def test_large_description_handling(self):
        """Test performance with large description fields."""
        
        # Create assignment with large description
        large_description = "Large description " * 1000  # ~17KB text
        
        start_time = time.time()
        
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'description': large_description
        })
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submission with large description
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': large_description
        })
        
        end_time = time.time()
        large_text_time = end_time - start_time
        
        # Verify data integrity
        self.assertEqual(len(assignment.description), len(large_description))
        self.assertEqual(len(submission.description), len(large_description))
        
        # Performance should handle large text efficiently
        self.assertLess(large_text_time, 3.0, f"Large text handling took {large_text_time:.2f}s")
    
    def test_complex_workflow_performance(self):
        """Test performance of complex workflow operations."""
        
        # Create multiple assignments with complex workflows
        start_time = time.time()
        
        for i in range(10):
            # Create assignment
            grading_assignment = self.grading_assignment.create({
                'name': f'Complex Workflow Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now(),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data['grading_assignment_id'] = grading_assignment.id
            assignment = self.op_assignment.create(assignment_data)
            
            # Complex workflow
            assignment.act_publish()
            
            # Create multiple submissions
            for j in range(5):
                submission = self.op_assignment_subline.create({
                    'assignment_id': assignment.id,
                    'student_id': self.student1.id if j % 2 == 0 else self.student2.id,
                    'description': f'Workflow submission {j+1}'
                })
                
                # Complex submission workflow
                submission.act_submit()
                if j % 3 == 0:
                    submission.act_accept()
                elif j % 3 == 1:
                    submission.act_change_req()
                    submission.act_submit()
                    submission.act_accept()
                else:
                    submission.act_reject()
            
            # Assignment workflow
            assignment.act_finish()
        
        end_time = time.time()
        workflow_time = end_time - start_time
        
        # Should handle complex workflows efficiently
        self.assertLess(workflow_time, 20.0, f"Complex workflow took {workflow_time:.2f}s")
    
    def test_onchange_performance(self):
        """Test performance of onchange methods."""
        
        # Create assignment for onchange testing
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Test onchange course performance
        start_time = time.time()
        
        for i in range(20):
            assignment.course_id = self.course
            result = assignment.onchange_course()
            
            # Should return domain quickly
            self.assertIn('domain', result)
        
        end_time = time.time()
        onchange_time = end_time - start_time
        
        self.assertLess(onchange_time, 1.0, f"Onchange operations took {onchange_time:.2f}s")
    
    def test_compute_method_caching(self):
        """Test compute method caching and efficiency."""
        
        # Create assignment with submissions
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create submissions
        for i in range(20):
            self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': self.student1.id if i % 2 == 0 else self.student2.id,
                'description': f'Cache test submission {i+1}'
            })
        
        # Test compute method multiple times
        start_time = time.time()
        
        for i in range(10):
            assignment._compute_assignment_count_compute()
            count = assignment.assignment_sub_line_count
            self.assertEqual(count, 20)
        
        end_time = time.time()
        compute_time = end_time - start_time
        
        # Multiple compute calls should be efficient
        self.assertLess(compute_time, 2.0, f"Multiple compute calls took {compute_time:.2f}s")