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

from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceCompute(TestAttendanceCommon):
    """Test attendance calculation and statistics computation."""

    def setUp(self):
        """Set up test data for attendance calculations."""
        super().setUp()
        
        # Create multiple attendance sheets for statistics
        self.sheet1 = self.create_attendance_sheet(attendance_date=self.today)
        self.sheet2 = self.create_attendance_sheet(attendance_date=self.yesterday)
        
        # Create attendance lines with different statuses
        self.line1_present = self.create_attendance_line(
            self.sheet1, self.student1, present=True)
        self.line1_absent = self.create_attendance_line(
            self.sheet1, self.student2, present=False)
        
        self.line2_present = self.create_attendance_line(
            self.sheet2, self.student1, present=True)
        self.line2_present2 = self.create_attendance_line(
            self.sheet2, self.student2, present=True)

    def test_attendance_register_statistics_computation(self):
        """Test attendance register statistics calculation."""
        # Force computation
        self.register._compute_attendance_statistics()
        
        self.assertEqual(self.register.attendance_sheet_count, 2,
                        "Should count 2 attendance sheets")
        self.assertEqual(self.register.total_students, 2,
                        "Should count 2 students in batch")

    def test_attendance_percentage_calculation(self):
        """Test student attendance percentage calculation."""
        # Add student attendance calculation method if it exists
        # This tests the compute method for attendance percentage
        
        # Get all attendance lines for student1
        student1_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        total_classes = len(student1_lines)
        present_classes = len(student1_lines.filtered('present'))
        expected_percentage = (present_classes / total_classes) * 100 if total_classes > 0 else 0
        
        self.assertEqual(total_classes, 2, "Student1 should have 2 attendance records")
        self.assertEqual(present_classes, 2, "Student1 should be present in all classes")
        self.assertEqual(expected_percentage, 100.0, "Student1 should have 100% attendance")

    def test_attendance_statistics_by_date_range(self):
        """Test attendance statistics for specific date ranges."""
        # Create additional sheets for broader date range
        from datetime import timedelta
        
        week_ago = self.today - timedelta(days=7)
        month_ago = self.today - timedelta(days=30)
        
        old_sheet = self.create_attendance_sheet(attendance_date=week_ago)
        very_old_sheet = self.create_attendance_sheet(attendance_date=month_ago)
        
        # Count sheets in different ranges
        all_sheets = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id)
        ])
        
        recent_sheets = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id),
            ('attendance_date', '>=', week_ago)
        ])
        
        self.assertEqual(len(all_sheets), 4, "Should have 4 total sheets")
        self.assertEqual(len(recent_sheets), 3, "Should have 3 recent sheets")

    def test_batch_attendance_statistics(self):
        """Test batch-level attendance statistics."""
        # Calculate batch attendance statistics
        total_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        present_lines = total_lines.filtered('present')
        absent_lines = total_lines.filtered('absent')
        
        self.assertEqual(len(total_lines), 4, "Should have 4 total attendance lines")
        self.assertEqual(len(present_lines), 3, "Should have 3 present lines")
        self.assertEqual(len(absent_lines), 1, "Should have 1 absent line")
        
        # Calculate percentages
        present_percentage = (len(present_lines) / len(total_lines)) * 100
        self.assertEqual(present_percentage, 75.0, "Batch should have 75% attendance")

    def test_student_attendance_summary(self):
        """Test individual student attendance summary."""
        # Student 1 summary
        student1_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student1.id),
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        student1_present = len(student1_lines.filtered('present'))
        student1_total = len(student1_lines)
        student1_percentage = (student1_present / student1_total) * 100 if student1_total > 0 else 0
        
        # Student 2 summary
        student2_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student2.id),
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        student2_present = len(student2_lines.filtered('present'))
        student2_total = len(student2_lines)
        student2_percentage = (student2_present / student2_total) * 100 if student2_total > 0 else 0
        
        self.assertEqual(student1_percentage, 100.0, "Student1 should have 100% attendance")
        self.assertEqual(student2_percentage, 50.0, "Student2 should have 50% attendance")

    def test_attendance_trend_analysis(self):
        """Test attendance trend analysis over time."""
        # Analyze attendance trends
        sheets_by_date = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id)
        ], order='attendance_date desc')
        
        trend_data = []
        for sheet in sheets_by_date:
            total_students = len(sheet.attendance_line)
            present_students = len(sheet.attendance_line.filtered('present'))
            percentage = (present_students / total_students) * 100 if total_students > 0 else 0
            
            trend_data.append({
                'date': sheet.attendance_date,
                'percentage': percentage,
                'present': present_students,
                'total': total_students
            })
        
        self.assertEqual(len(trend_data), 2, "Should have 2 data points")
        
        # Check today's attendance
        today_data = next((d for d in trend_data if d['date'] == self.today), None)
        self.assertIsNotNone(today_data, "Should have today's data")
        self.assertEqual(today_data['percentage'], 50.0, "Today should have 50% attendance")
        
        # Check yesterday's attendance
        yesterday_data = next((d for d in trend_data if d['date'] == self.yesterday), None)
        self.assertIsNotNone(yesterday_data, "Should have yesterday's data")
        self.assertEqual(yesterday_data['percentage'], 100.0, "Yesterday should have 100% attendance")

    def test_attendance_absence_patterns(self):
        """Test analysis of student absence patterns."""
        # Find students with low attendance
        all_students = [self.student1, self.student2]
        low_attendance_threshold = 75.0
        low_attendance_students = []
        
        for student in all_students:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            if lines:
                present_count = len(lines.filtered('present'))
                total_count = len(lines)
                percentage = (present_count / total_count) * 100
                
                if percentage < low_attendance_threshold:
                    low_attendance_students.append({
                        'student': student,
                        'percentage': percentage,
                        'absent_days': total_count - present_count
                    })
        
        self.assertEqual(len(low_attendance_students), 1, 
                        "Should identify 1 student with low attendance")
        self.assertEqual(low_attendance_students[0]['student'], self.student2,
                        "Student2 should have low attendance")

    def test_attendance_monthly_summary(self):
        """Test monthly attendance summary calculations."""
        # Group attendance by month
        from datetime import date
        
        current_month = self.today.month
        current_year = self.today.year
        
        monthly_sheets = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id),
            ('attendance_date', '>=', date(current_year, current_month, 1)),
            ('attendance_date', '<', date(current_year, current_month + 1, 1) if current_month < 12 
             else date(current_year + 1, 1, 1))
        ])
        
        monthly_lines = self.env['op.attendance.line'].search([
            ('attendance_id', 'in', monthly_sheets.ids)
        ])
        
        monthly_present = len(monthly_lines.filtered('present'))
        monthly_total = len(monthly_lines)
        monthly_percentage = (monthly_present / monthly_total) * 100 if monthly_total > 0 else 0
        
        self.assertGreater(len(monthly_sheets), 0, "Should have sheets in current month")
        self.assertGreater(monthly_total, 0, "Should have attendance lines in current month")

    def test_attendance_comparison_analysis(self):
        """Test comparative attendance analysis between students."""
        # Compare attendance between students
        student_comparisons = []
        
        for student in [self.student1, self.student2]:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            present_count = len(lines.filtered('present'))
            total_count = len(lines)
            percentage = (present_count / total_count) * 100 if total_count > 0 else 0
            
            student_comparisons.append({
                'student_id': student.id,
                'student_name': student.name,
                'percentage': percentage,
                'present_days': present_count,
                'total_days': total_count
            })
        
        # Sort by attendance percentage
        student_comparisons.sort(key=lambda x: x['percentage'], reverse=True)
        
        self.assertEqual(student_comparisons[0]['student_id'], self.student1.id,
                        "Student1 should have highest attendance")
        self.assertEqual(student_comparisons[0]['percentage'], 100.0,
                        "Highest attendance should be 100%")

    def test_attendance_computation_performance(self):
        """Test performance of attendance computations with larger datasets."""
        # Create additional test data
        additional_students = []
        for i in range(10):
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
            additional_students.append(student)
        
        # Create attendance lines for additional students
        for student in additional_students:
            self.create_attendance_line(self.sheet1, student, present=True)
            self.create_attendance_line(self.sheet2, student, present=i % 2 == 0)  # Alternate attendance
        
        # Test computation performance
        start_time = self.env.now()
        
        # Recalculate statistics
        self.register._compute_attendance_statistics()
        
        # Calculate batch statistics
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        present_lines = all_lines.filtered('present')
        attendance_percentage = (len(present_lines) / len(all_lines)) * 100 if all_lines else 0
        
        end_time = self.env.now()
        computation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertLess(computation_time, 5.0, "Computation should complete within 5 seconds")
        self.assertGreater(len(all_lines), 20, "Should have processed many attendance lines")
        self.assertIsInstance(attendance_percentage, (int, float), "Should calculate valid percentage")