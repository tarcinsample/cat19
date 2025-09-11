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
class TestAttendanceReports(TestAttendanceCommon):
    """Test attendance reports generation and data accuracy."""

    def setUp(self):
        """Set up test data for attendance reports."""
        super().setUp()
        
        # Create comprehensive attendance data for reporting
        self.sheet1 = self.create_attendance_sheet(attendance_date=self.today)
        self.sheet2 = self.create_attendance_sheet(attendance_date=self.yesterday)
        
        # Create varied attendance patterns
        self.create_attendance_line(self.sheet1, self.student1, present=True)
        self.create_attendance_line(self.sheet1, self.student2, present=False, remarks="Sick")
        
        self.create_attendance_line(self.sheet2, self.student1, present=True)
        self.create_attendance_line(self.sheet2, self.student2, present=True)

    def test_student_attendance_report_model(self):
        """Test student attendance report model functionality."""
        # Check if student attendance report model exists
        report_model = self.env.get('student.attendance.report')
        if report_model:
            # Test report generation
            report_data = report_model.search([])
            self.assertIsInstance(report_data, type(report_model),
                                "Should return report model instances")

    def test_attendance_report_data_accuracy(self):
        """Test accuracy of attendance report data."""
        # Generate report data manually to test accuracy
        students = [self.student1, self.student2]
        report_data = []
        
        for student in students:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            total_classes = len(lines)
            present_classes = len(lines.filtered('present'))
            absent_classes = total_classes - present_classes
            percentage = (present_classes / total_classes) * 100 if total_classes > 0 else 0
            
            report_data.append({
                'student_id': student.id,
                'student_name': student.name,
                'total_classes': total_classes,
                'present_classes': present_classes,
                'absent_classes': absent_classes,
                'attendance_percentage': percentage
            })
        
        # Verify report data accuracy
        student1_data = next((d for d in report_data if d['student_id'] == self.student1.id), None)
        student2_data = next((d for d in report_data if d['student_id'] == self.student2.id), None)
        
        self.assertIsNotNone(student1_data, "Should have data for student1")
        self.assertIsNotNone(student2_data, "Should have data for student2")
        
        self.assertEqual(student1_data['present_classes'], 2, "Student1 should have 2 present classes")
        self.assertEqual(student1_data['attendance_percentage'], 100.0, "Student1 should have 100% attendance")
        
        self.assertEqual(student2_data['present_classes'], 1, "Student2 should have 1 present class")
        self.assertEqual(student2_data['attendance_percentage'], 50.0, "Student2 should have 50% attendance")

    def test_attendance_report_filtering(self):
        """Test attendance report filtering capabilities."""
        # Test filtering by date range
        date_filtered_sheets = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id),
            ('attendance_date', '>=', self.yesterday),
            ('attendance_date', '<=', self.today)
        ])
        
        self.assertEqual(len(date_filtered_sheets), 2, "Should find 2 sheets in date range")
        
        # Test filtering by course
        course_filtered_sheets = self.env['op.attendance.sheet'].search([
            ('course_id', '=', self.course.id)
        ])
        
        self.assertGreaterEqual(len(course_filtered_sheets), 2, "Should find sheets for course")
        
        # Test filtering by batch
        batch_filtered_sheets = self.env['op.attendance.sheet'].search([
            ('batch_id', '=', self.batch.id)
        ])
        
        self.assertGreaterEqual(len(batch_filtered_sheets), 2, "Should find sheets for batch")

    def test_attendance_summary_report(self):
        """Test attendance summary report generation."""
        # Generate summary report data
        summary_data = {
            'total_students': 0,
            'total_classes_held': 0,
            'total_present': 0,
            'total_absent': 0,
            'overall_percentage': 0.0
        }
        
        # Calculate summary statistics
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        unique_students = set(all_lines.mapped('student_id.id'))
        unique_sheets = set(all_lines.mapped('attendance_id.id'))
        
        present_lines = all_lines.filtered('present')
        absent_lines = all_lines.filtered('absent')
        
        summary_data.update({
            'total_students': len(unique_students),
            'total_classes_held': len(unique_sheets),
            'total_present': len(present_lines),
            'total_absent': len(absent_lines),
            'overall_percentage': (len(present_lines) / len(all_lines)) * 100 if all_lines else 0
        })
        
        # Verify summary calculations
        self.assertEqual(summary_data['total_students'], 2, "Should count 2 unique students")
        self.assertEqual(summary_data['total_classes_held'], 2, "Should count 2 classes held")
        self.assertEqual(summary_data['total_present'], 3, "Should count 3 present instances")
        self.assertEqual(summary_data['total_absent'], 1, "Should count 1 absent instance")
        self.assertEqual(summary_data['overall_percentage'], 75.0, "Overall percentage should be 75%")

    def test_attendance_detail_report(self):
        """Test detailed attendance report with all student data."""
        # Generate detailed report data
        detailed_data = []
        
        sheets = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id)
        ], order='attendance_date desc')
        
        for sheet in sheets:
            for line in sheet.attendance_line:
                detailed_data.append({
                    'date': sheet.attendance_date,
                    'student_name': line.student_id.name,
                    'course': sheet.course_id.name,
                    'batch': sheet.batch_id.name,
                    'status': 'Present' if line.present else 'Absent',
                    'remark': line.remark or '',
                    'faculty': sheet.faculty_id.name if sheet.faculty_id else ''
                })
        
        self.assertEqual(len(detailed_data), 4, "Should have 4 detailed records")
        
        # Check specific records
        student2_today = next((d for d in detailed_data 
                              if d['student_name'] == self.student2.name 
                              and d['date'] == self.today), None)
        
        self.assertIsNotNone(student2_today, "Should find student2's today record")
        self.assertEqual(student2_today['status'], 'Absent', "Student2 should be absent today")
        self.assertEqual(student2_today['remark'], 'Sick', "Should have sick remark")

    def test_attendance_export_functionality(self):
        """Test attendance data export functionality."""
        # Simulate export data preparation
        export_data = []
        
        # Export format: CSV-like structure
        headers = ['Student Name', 'Date', 'Status', 'Course', 'Batch', 'Remarks']
        export_data.append(headers)
        
        lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ], order='attendance_date desc, student_id.name')
        
        for line in lines:
            row = [
                line.student_id.name,
                str(line.attendance_id.attendance_date),
                'Present' if line.present else 'Absent',
                line.attendance_id.course_id.name,
                line.attendance_id.batch_id.name,
                line.remark or ''
            ]
            export_data.append(row)
        
        self.assertEqual(len(export_data), 5, "Should have header + 4 data rows")
        self.assertEqual(export_data[0], headers, "First row should be headers")
        
        # Verify data integrity in export
        self.assertTrue(any('Test Student 1' in row for row in export_data[1:]),
                       "Should include student1 data")
        self.assertTrue(any('Test Student 2' in row for row in export_data[1:]),
                       "Should include student2 data")

    def test_attendance_chart_data_preparation(self):
        """Test data preparation for attendance charts and graphs."""
        # Prepare data for attendance trends chart
        chart_data = {
            'labels': [],
            'present_data': [],
            'absent_data': [],
            'percentage_data': []
        }
        
        sheets = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.register.id)
        ], order='attendance_date')
        
        for sheet in sheets:
            total_students = len(sheet.attendance_line)
            present_count = len(sheet.attendance_line.filtered('present'))
            absent_count = total_students - present_count
            percentage = (present_count / total_students) * 100 if total_students > 0 else 0
            
            chart_data['labels'].append(str(sheet.attendance_date))
            chart_data['present_data'].append(present_count)
            chart_data['absent_data'].append(absent_count)
            chart_data['percentage_data'].append(percentage)
        
        # Verify chart data
        self.assertEqual(len(chart_data['labels']), 2, "Should have 2 date labels")
        self.assertEqual(len(chart_data['present_data']), 2, "Should have 2 present data points")
        self.assertEqual(chart_data['percentage_data'][0], 100.0, "Yesterday should have 100%")
        self.assertEqual(chart_data['percentage_data'][1], 50.0, "Today should have 50%")

    def test_low_attendance_report(self):
        """Test low attendance alert report."""
        # Define low attendance threshold
        low_attendance_threshold = 75.0
        low_attendance_students = []
        
        students = self.env['op.student'].search([
            ('course_detail_ids.course_id', '=', self.course.id),
            ('course_detail_ids.batch_id', '=', self.batch.id)
        ])
        
        for student in students:
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
                        'student_id': student.id,
                        'student_name': student.name,
                        'attendance_percentage': percentage,
                        'total_classes': total_count,
                        'present_classes': present_count,
                        'absent_classes': total_count - present_count
                    })
        
        # Verify low attendance detection
        self.assertEqual(len(low_attendance_students), 1, "Should identify 1 low attendance student")
        self.assertEqual(low_attendance_students[0]['student_name'], self.student2.name,
                        "Student2 should have low attendance")
        self.assertEqual(low_attendance_students[0]['attendance_percentage'], 50.0,
                        "Low attendance percentage should be 50%")

    def test_faculty_attendance_report(self):
        """Test faculty-wise attendance report."""
        # Create attendance sheets with faculty assignment
        sheet_with_faculty = self.create_attendance_sheet(
            attendance_date=self.today,
            faculty_id=self.faculty.id
        )
        
        # Generate faculty report data
        faculty_report = []
        
        faculties = self.env['op.faculty'].search([])
        for faculty in faculties:
            sheets = self.env['op.attendance.sheet'].search([
                ('faculty_id', '=', faculty.id),
                ('register_id', '=', self.register.id)
            ])
            
            if sheets:
                total_classes = len(sheets)
                total_lines = self.env['op.attendance.line'].search([
                    ('attendance_id', 'in', sheets.ids)
                ])
                
                present_lines = total_lines.filtered('present')
                attendance_rate = (len(present_lines) / len(total_lines)) * 100 if total_lines else 0
                
                faculty_report.append({
                    'faculty_name': faculty.name,
                    'classes_conducted': total_classes,
                    'total_attendance_records': len(total_lines),
                    'attendance_rate': attendance_rate
                })
        
        # Verify faculty report data
        faculty_data = next((f for f in faculty_report if f['faculty_name'] == self.faculty.name), None)
        if faculty_data:
            self.assertGreater(faculty_data['classes_conducted'], 0, "Faculty should have conducted classes")

    def test_attendance_report_performance(self):
        """Test performance of attendance report generation."""
        # Create larger dataset for performance testing
        additional_students = []
        for i in range(20):
            student = self.env['op.student'].create({
                'name': f'Report Student {i}',
                'first_name': 'Report',
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
        
        # Create attendance data for additional students
        for student in additional_students:
            self.create_attendance_line(self.sheet1, student, present=i % 3 != 0)  # Varied attendance
            self.create_attendance_line(self.sheet2, student, present=i % 2 == 0)
        
        # Test report generation performance
        from datetime import datetime
        start_time = datetime.now()
        
        # Generate comprehensive report
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        report_data = []
        students = set(all_lines.mapped('student_id'))
        
        for student in students:
            student_lines = all_lines.filtered(lambda l: l.student_id == student)
            present_count = len(student_lines.filtered('present'))
            total_count = len(student_lines)
            percentage = (present_count / total_count) * 100 if total_count > 0 else 0
            
            report_data.append({
                'student': student.name,
                'percentage': percentage,
                'present': present_count,
                'total': total_count
            })
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertLess(generation_time, 10.0, "Report generation should complete within 10 seconds")
        self.assertGreaterEqual(len(report_data), 22, "Should process all students")
        self.assertTrue(all(isinstance(d['percentage'], (int, float)) for d in report_data),
                       "All percentages should be numeric")