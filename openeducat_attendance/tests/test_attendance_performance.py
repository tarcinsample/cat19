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

from datetime import timedelta, datetime
from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendancePerformance(TestAttendanceCommon):
    """Test attendance analytics performance with large datasets."""

    def setUp(self):
        """Set up large dataset for performance testing."""
        super().setUp()
        
        # Create large number of students
        self.large_student_count = 100
        self.large_students = []
        
        for i in range(self.large_student_count):
            student = self.env['op.student'].create({
                'name': f'Performance Student {i}',
                'first_name': 'Performance',
                'last_name': f'Student{i}',
                'birth_date': self.yesterday,
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            self.large_students.append(student)
        
        # Create large number of attendance sheets (30 days)
        self.large_sheets = []
        for day in range(30):
            date = self.today - timedelta(days=day)
            sheet = self.create_attendance_sheet(attendance_date=date)
            self.large_sheets.append(sheet)
        
        # Create attendance lines for all combinations
        self._create_large_attendance_dataset()

    def _create_large_attendance_dataset(self):
        """Create large attendance dataset efficiently."""
        # Use batch creation for better performance
        attendance_data = []
        
        for sheet in self.large_sheets:
            for i, student in enumerate(self.large_students):
                # Create varied attendance patterns
                present = (i + sheet.id) % 3 != 0  # ~67% attendance
                vals = {
                    'attendance_id': sheet.id,
                    'student_id': student.id,
                    'present': present,
                    'remark': f'Perf test {i}' if i % 10 == 0 else False
                }
                # Set absent status when not present
                if not present:
                    vals['absent'] = True
                attendance_data.append(vals)
        
        # Batch create all attendance lines
        self.env['op.attendance.line'].create(attendance_data)
        
        # Verify dataset size
        total_expected = self.large_student_count * len(self.large_sheets)
        actual_count = self.env['op.attendance.line'].search_count([
            ('attendance_id', 'in', [s.id for s in self.large_sheets])
        ])
        
        self.assertEqual(actual_count, total_expected,
                        f"Should create {total_expected} attendance records")

    def test_large_dataset_query_performance(self):
        """Test query performance with large attendance dataset."""
        start_time = datetime.now()
        
        # Test complex query performance
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        expected_count = self.large_student_count * len(self.large_sheets)
        self.assertEqual(len(all_lines), expected_count,
                        f"Should retrieve {expected_count} records")
        self.assertLess(query_time, 10.0,
                       "Large dataset query should complete within 10 seconds")

    def test_attendance_percentage_calculation_performance(self):
        """Test performance of attendance percentage calculations."""
        start_time = datetime.now()
        
        # Calculate attendance percentage for all students
        student_percentages = {}
        
        for student in self.large_students:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            present_count = len(lines.filtered('present'))
            total_count = len(lines)
            percentage = (present_count / total_count) * 100 if total_count > 0 else 0
            student_percentages[student.id] = percentage
        
        end_time = datetime.now()
        calculation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(student_percentages), self.large_student_count,
                        f"Should calculate percentage for {self.large_student_count} students")
        self.assertLess(calculation_time, 15.0,
                       "Percentage calculation should complete within 15 seconds")
        
        # Verify calculation accuracy
        sample_percentage = list(student_percentages.values())[0]
        self.assertIsInstance(sample_percentage, (int, float),
                             "Percentage should be numeric")
        self.assertGreaterEqual(sample_percentage, 0,
                               "Percentage should be non-negative")
        self.assertLessEqual(sample_percentage, 100,
                            "Percentage should not exceed 100")

    def test_attendance_aggregation_performance(self):
        """Test performance of attendance data aggregation."""
        start_time = datetime.now()
        
        # Aggregate attendance by date
        date_aggregations = {}
        
        for sheet in self.large_sheets:
            lines = self.env['op.attendance.line'].search([
                ('attendance_id', '=', sheet.id)
            ])
            
            total_students = len(lines)
            present_students = len(lines.filtered('present'))
            absent_students = total_students - present_students
            attendance_rate = (present_students / total_students) * 100 if total_students > 0 else 0
            
            date_aggregations[sheet.attendance_date] = {
                'total_students': total_students,
                'present_students': present_students,
                'absent_students': absent_students,
                'attendance_rate': attendance_rate
            }
        
        end_time = datetime.now()
        aggregation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(date_aggregations), len(self.large_sheets),
                        "Should aggregate data for all dates")
        self.assertLess(aggregation_time, 12.0,
                       "Aggregation should complete within 12 seconds")
        
        # Verify aggregation accuracy
        sample_agg = list(date_aggregations.values())[0]
        self.assertEqual(sample_agg['total_students'], self.large_student_count,
                        "Should count all students per date")

    def test_bulk_attendance_update_performance(self):
        """Test performance of bulk attendance updates."""
        # Get subset of attendance lines for update
        lines_to_update = self.env['op.attendance.line'].search([
            ('attendance_id', 'in', self.large_sheets[:5].ids),  # First 5 sheets
            ('present', '=', False)
        ])
        
        start_time = datetime.now()
        
        # Bulk update attendance status
        lines_to_update.write({
            'present': True,
            'remark': 'Bulk updated for performance test'
        })
        
        end_time = datetime.now()
        update_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertGreater(len(lines_to_update), 0,
                          "Should have lines to update")
        self.assertLess(update_time, 8.0,
                       "Bulk update should complete within 8 seconds")
        
        # Verify update success
        updated_lines = self.env['op.attendance.line'].browse(lines_to_update.ids)
        all_updated = all(line.present for line in updated_lines)
        self.assertTrue(all_updated, "All updated lines should be present")

    def test_attendance_search_with_complex_filters(self):
        """Test performance of complex attendance searches."""
        start_time = datetime.now()
        
        # Complex search with multiple conditions
        complex_search = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id),
            ('attendance_date', '>=', self.today - timedelta(days=15)),
            ('attendance_date', '<=', self.today),
            ('present', '=', True),
            ('student_id.name', 'ilike', 'Performance')
        ])
        
        end_time = datetime.now()
        search_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertGreater(len(complex_search), 0,
                          "Complex search should return results")
        self.assertLess(search_time, 5.0,
                       "Complex search should complete within 5 seconds")

    def test_attendance_statistics_computation_performance(self):
        """Test performance of statistics computation."""
        start_time = datetime.now()
        
        # Compute various statistics
        statistics = {
            'total_students': len(self.large_students),
            'total_classes': len(self.large_sheets),
            'total_attendance_records': 0,
            'overall_attendance_rate': 0,
            'daily_averages': [],
            'student_averages': []
        }
        
        # Count total records
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        statistics['total_attendance_records'] = len(all_lines)
        
        # Calculate overall attendance rate
        present_lines = all_lines.filtered('present')
        statistics['overall_attendance_rate'] = (len(present_lines) / len(all_lines)) * 100 if all_lines else 0
        
        # Calculate daily averages (sample of 10 days for performance)
        sample_sheets = self.large_sheets[:10]
        for sheet in sample_sheets:
            sheet_lines = all_lines.filtered(lambda l: l.attendance_id == sheet)
            if sheet_lines:
                present_count = len(sheet_lines.filtered('present'))
                daily_rate = (present_count / len(sheet_lines)) * 100
                statistics['daily_averages'].append({
                    'date': sheet.attendance_date,
                    'rate': daily_rate
                })
        
        # Calculate student averages (sample of 20 students for performance)
        sample_students = self.large_students[:20]
        for student in sample_students:
            student_lines = all_lines.filtered(lambda l: l.student_id == student)
            if student_lines:
                present_count = len(student_lines.filtered('present'))
                student_rate = (present_count / len(student_lines)) * 100
                statistics['student_averages'].append({
                    'student_id': student.id,
                    'rate': student_rate
                })
        
        end_time = datetime.now()
        computation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        expected_records = self.large_student_count * len(self.large_sheets)
        self.assertEqual(statistics['total_attendance_records'], expected_records,
                        "Should count all attendance records")
        self.assertLess(computation_time, 20.0,
                       "Statistics computation should complete within 20 seconds")
        
        # Verify statistics accuracy
        self.assertGreater(statistics['overall_attendance_rate'], 0,
                          "Overall attendance rate should be positive")
        self.assertEqual(len(statistics['daily_averages']), 10,
                        "Should compute 10 daily averages")
        self.assertEqual(len(statistics['student_averages']), 20,
                        "Should compute 20 student averages")

    def test_attendance_report_generation_performance(self):
        """Test performance of comprehensive report generation."""
        start_time = datetime.now()
        
        # Generate comprehensive attendance report
        report_data = {
            'generated_at': datetime.now(),
            'period': {
                'start_date': self.today - timedelta(days=29),
                'end_date': self.today
            },
            'summary': {},
            'detailed_data': [],
            'charts_data': {}
        }
        
        # Summary section
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        present_lines = all_lines.filtered('present')
        report_data['summary'] = {
            'total_students': len(set(all_lines.mapped('student_id.id'))),
            'total_classes': len(set(all_lines.mapped('attendance_id.id'))),
            'total_present': len(present_lines),
            'total_absent': len(all_lines) - len(present_lines),
            'overall_percentage': (len(present_lines) / len(all_lines)) * 100 if all_lines else 0
        }
        
        # Detailed data (sample for performance)
        sample_lines = all_lines[:100]  # Sample for performance
        for line in sample_lines:
            report_data['detailed_data'].append({
                'student_name': line.student_id.name,
                'date': str(line.attendance_date),
                'status': 'Present' if line.present else 'Absent',
                'remark': line.remark or ''
            })
        
        # Charts data (weekly aggregation for performance)
        weeks_data = {}
        for sheet in self.large_sheets[::7]:  # Every 7th sheet for weekly view
            sheet_lines = all_lines.filtered(lambda l: l.attendance_id == sheet)
            if sheet_lines:
                present_count = len(sheet_lines.filtered('present'))
                total_count = len(sheet_lines)
                weeks_data[str(sheet.attendance_date)] = {
                    'present': present_count,
                    'total': total_count,
                    'percentage': (present_count / total_count) * 100
                }
        
        report_data['charts_data'] = weeks_data
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertLess(generation_time, 25.0,
                       "Report generation should complete within 25 seconds")
        self.assertGreater(report_data['summary']['total_students'], 0,
                          "Report should include student data")
        self.assertGreater(len(report_data['detailed_data']), 0,
                          "Report should include detailed data")
        self.assertGreater(len(report_data['charts_data']), 0,
                          "Report should include chart data")

    def test_memory_usage_with_large_dataset(self):
        """Test memory efficiency with large attendance dataset."""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_queries = []
        for i in range(5):
            lines = self.env['op.attendance.line'].search([
                ('attendance_id.register_id', '=', self.register.id)
            ])
            large_queries.append(len(lines))
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory efficiency assertions
        self.assertLess(memory_increase, 100.0,
                       "Memory increase should be less than 100MB")
        self.assertTrue(all(q > 0 for q in large_queries),
                       "All queries should return results")

    def test_database_connection_efficiency(self):
        """Test database connection efficiency with large operations."""
        start_time = datetime.now()
        
        # Perform multiple database operations
        operation_count = 0
        
        # Batch read operations
        for i in range(0, len(self.large_students), 10):
            student_batch = self.large_students[i:i+10]
            student_ids = [s.id for s in student_batch]
            
            lines = self.env['op.attendance.line'].search([
                ('student_id', 'in', student_ids),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            operation_count += 1
        
        end_time = datetime.now()
        operation_time = (end_time - start_time).total_seconds()
        
        # Efficiency assertions
        self.assertGreater(operation_count, 0, "Should perform multiple operations")
        self.assertLess(operation_time, 15.0,
                       "Batch operations should complete within 15 seconds")
        
        # Calculate operations per second
        ops_per_second = operation_count / operation_time if operation_time > 0 else 0
        self.assertGreater(ops_per_second, 1.0,
                          "Should maintain reasonable operation throughput")

    def test_concurrent_access_simulation(self):
        """Test performance under simulated concurrent access."""
        start_time = datetime.now()
        
        # Simulate concurrent read/write operations
        operations = []
        
        # Simulate multiple users reading attendance
        for i in range(10):
            lines = self.env['op.attendance.line'].search([
                ('attendance_id.register_id', '=', self.register.id),
                ('attendance_date', '=', self.today - timedelta(days=i))
            ])
            operations.append(('read', len(lines)))
        
        # Simulate concurrent updates
        update_lines = self.env['op.attendance.line'].search([
            ('attendance_id', 'in', self.large_sheets[:3].ids),
            ('present', '=', False)
        ], limit=50)
        
        if update_lines:
            update_lines.write({'remark': 'Concurrent test update'})
            operations.append(('update', len(update_lines)))
        
        end_time = datetime.now()
        concurrent_time = (end_time - start_time).total_seconds()
        
        # Concurrency performance assertions
        self.assertGreater(len(operations), 10,
                          "Should perform multiple concurrent operations")
        self.assertLess(concurrent_time, 10.0,
                       "Concurrent operations should complete within 10 seconds")
        
        # Verify data integrity after concurrent operations
        final_count = self.env['op.attendance.line'].search_count([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        expected_count = self.large_student_count * len(self.large_sheets)
        self.assertEqual(final_count, expected_count,
                        "Data integrity should be maintained during concurrent access")