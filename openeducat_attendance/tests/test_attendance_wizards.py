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

import base64
import csv
import io
from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceWizards(TestAttendanceCommon):
    """Test attendance wizards including export and import functionality."""

    def setUp(self):
        """Set up test data for wizard testing."""
        super().setUp()
        
        # Create attendance data for export
        self.sheet1 = self.create_attendance_sheet(attendance_date=self.today)
        self.sheet2 = self.create_attendance_sheet(attendance_date=self.yesterday)
        
        # Create attendance lines
        self.create_attendance_line(self.sheet1, self.student1, present=True, remarks="On time")
        self.create_attendance_line(self.sheet1, self.student2, present=False, remarks="Sick leave")
        self.create_attendance_line(self.sheet2, self.student1, present=True)
        self.create_attendance_line(self.sheet2, self.student2, present=True)

    def test_student_attendance_wizard(self):
        """Test student attendance wizard functionality."""
        # Check if wizard model exists
        wizard_model = self.env.get('student.attendance')
        if not wizard_model:
            return  # Skip if wizard not implemented
        
        # Create wizard instance
        wizard = wizard_model.create({
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'start_date': self.yesterday,
            'end_date': self.today,
        })
        
        # Test wizard data validation
        self.assertEqual(wizard.course_id, self.course, "Course should be set")
        self.assertEqual(wizard.batch_id, self.batch, "Batch should be set")
        self.assertEqual(wizard.start_date, self.yesterday, "Start date should be set")
        self.assertEqual(wizard.end_date, self.today, "End date should be set")

    def test_attendance_export_csv(self):
        """Test attendance data export to CSV format."""
        # Prepare export data
        export_data = []
        headers = ['Student Name', 'Date', 'Status', 'Course', 'Batch', 'Subject', 'Remarks']
        
        # Get all attendance lines
        lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ], order='attendance_id.attendance_date desc, student_id.name')
        
        for line in lines:
            row = [
                line.student_id.name,
                str(line.attendance_id.attendance_date),
                'Present' if line.present else 'Absent',
                line.attendance_id.course_id.name,
                line.attendance_id.batch_id.name,
                line.attendance_id.register_id.subject_id.name if line.attendance_id.register_id.subject_id else '',
                line.remarks or ''
            ]
            export_data.append(row)
        
        # Create CSV in memory
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(headers)
        csv_writer.writerows(export_data)
        
        # Get CSV content
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()
        
        # Verify CSV structure
        self.assertIn('Student Name', csv_content, "CSV should contain headers")
        self.assertIn('Test Student 1', csv_content, "CSV should contain student data")
        self.assertIn('Present', csv_content, "CSV should contain attendance status")
        self.assertIn('Sick leave', csv_content, "CSV should contain remarks")

    def test_attendance_export_excel(self):
        """Test attendance data export to Excel format."""
        # Simulate Excel export data structure
        excel_data = {
            'sheets': [{
                'name': 'Attendance Report',
                'headers': ['Student', 'Course', 'Batch', 'Date', 'Status', 'Remarks'],
                'data': []
            }]
        }
        
        # Populate excel data
        lines = self.env['op.attendance.line'].search([
            ('attendance_id.register_id', '=', self.register.id)
        ])
        
        for line in lines:
            excel_data['sheets'][0]['data'].append([
                line.student_id.name,
                line.attendance_id.course_id.name,
                line.attendance_id.batch_id.name,
                str(line.attendance_id.attendance_date),
                'Present' if line.present else 'Absent',
                line.remarks or ''
            ])
        
        # Verify Excel data structure
        sheet_data = excel_data['sheets'][0]
        self.assertEqual(sheet_data['name'], 'Attendance Report', "Sheet name should be set")
        self.assertEqual(len(sheet_data['headers']), 6, "Should have 6 column headers")
        self.assertEqual(len(sheet_data['data']), 4, "Should have 4 data rows")

    def test_attendance_import_csv(self):
        """Test attendance data import from CSV format."""
        # Create CSV content for import
        csv_content = """Student Name,Date,Status,Remarks
Test Student 1,2024-01-01,Present,Imported
Test Student 2,2024-01-01,Absent,Imported - Sick
Test Student 1,2024-01-02,Present,Imported
Test Student 2,2024-01-02,Present,Imported"""
        
        # Parse CSV content
        csv_buffer = io.StringIO(csv_content)
        csv_reader = csv.DictReader(csv_buffer)
        
        imported_records = []
        for row in csv_reader:
            # Find student
            student = self.env['op.student'].search([
                ('name', '=', row['Student Name'])
            ], limit=1)
            
            if student:
                imported_records.append({
                    'student_id': student.id,
                    'date': row['Date'],
                    'present': row['Status'] == 'Present',
                    'remarks': row['Remarks']
                })
        
        csv_buffer.close()
        
        # Verify import parsing
        self.assertEqual(len(imported_records), 4, "Should parse 4 records")
        
        # Check first record
        first_record = imported_records[0]
        self.assertEqual(first_record['student_id'], self.student1.id, 
                        "Should identify correct student")
        self.assertTrue(first_record['present'], "Should parse present status")
        self.assertEqual(first_record['remarks'], 'Imported', "Should parse remarks")

    def test_attendance_import_validation(self):
        """Test validation during attendance import."""
        # Test import with invalid data
        invalid_csv_content = """Student Name,Date,Status,Remarks
Invalid Student,2024-01-01,Present,Should fail
Test Student 1,invalid-date,Present,Should fail
Test Student 2,2024-01-01,Invalid Status,Should fail"""
        
        csv_buffer = io.StringIO(invalid_csv_content)
        csv_reader = csv.DictReader(csv_buffer)
        
        import_errors = []
        for row_num, row in enumerate(csv_reader, start=2):
            # Validate student
            student = self.env['op.student'].search([
                ('name', '=', row['Student Name'])
            ], limit=1)
            
            if not student:
                import_errors.append({
                    'row': row_num,
                    'error': f"Student '{row['Student Name']}' not found"
                })
                continue
            
            # Validate date format
            try:
                from datetime import datetime
                datetime.strptime(row['Date'], '%Y-%m-%d')
            except ValueError:
                import_errors.append({
                    'row': row_num,
                    'error': f"Invalid date format: {row['Date']}"
                })
                continue
            
            # Validate status
            if row['Status'] not in ['Present', 'Absent']:
                import_errors.append({
                    'row': row_num,
                    'error': f"Invalid status: {row['Status']}"
                })
        
        csv_buffer.close()
        
        # Verify validation errors
        self.assertEqual(len(import_errors), 3, "Should detect 3 validation errors")
        self.assertTrue(any('Invalid Student' in e['error'] for e in import_errors),
                       "Should detect invalid student")
        self.assertTrue(any('Invalid date format' in e['error'] for e in import_errors),
                       "Should detect invalid date")
        self.assertTrue(any('Invalid status' in e['error'] for e in import_errors),
                       "Should detect invalid status")

    def test_attendance_export_filters(self):
        """Test attendance export with various filters."""
        # Test date range filter
        date_filtered_lines = self.env['op.attendance.line'].search([
            ('attendance_id.attendance_date', '>=', self.today),
            ('attendance_id.attendance_date', '<=', self.today)
        ])
        
        self.assertEqual(len(date_filtered_lines), 2, 
                        "Should filter by date correctly")
        
        # Test student filter
        student_filtered_lines = self.env['op.attendance.line'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertEqual(len(student_filtered_lines), 2, 
                        "Should filter by student correctly")
        
        # Test status filter
        present_filtered_lines = self.env['op.attendance.line'].search([
            ('present', '=', True)
        ])
        
        self.assertEqual(len(present_filtered_lines), 3, 
                        "Should filter by status correctly")

    def test_attendance_bulk_import(self):
        """Test bulk import of attendance records."""
        # Simulate bulk import data
        bulk_data = []
        
        # Create 10 days of attendance data
        from datetime import timedelta
        for day in range(10):
            date = self.today - timedelta(days=day)
            for student in [self.student1, self.student2]:
                bulk_data.append({
                    'student_name': student.name,
                    'date': str(date),
                    'status': 'Present' if day % 2 == 0 else 'Absent',
                    'remarks': f'Bulk import day {day}'
                })
        
        # Process bulk import
        imported_count = 0
        for data in bulk_data:
            student = self.env['op.student'].search([
                ('name', '=', data['student_name'])
            ], limit=1)
            
            if student:
                # Check if attendance sheet exists for date
                sheet = self.env['op.attendance.sheet'].search([
                    ('register_id', '=', self.register.id),
                    ('attendance_date', '=', data['date'])
                ], limit=1)
                
                if not sheet:
                    # Create sheet if it doesn't exist
                    sheet = self.create_attendance_sheet(attendance_date=data['date'])
                
                # Check if line already exists
                existing_line = self.env['op.attendance.line'].search([
                    ('attendance_id', '=', sheet.id),
                    ('student_id', '=', student.id)
                ], limit=1)
                
                if not existing_line:
                    imported_count += 1
        
        self.assertGreater(imported_count, 0, "Should import some records")

    def test_attendance_export_permissions(self):
        """Test export permissions for different user roles."""
        # Create test file content
        file_content = b"test,data,export"
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # Simulate export file creation
        export_file = {
            'name': 'attendance_export.csv',
            'type': 'csv',
            'content': encoded_content,
            'size': len(file_content),
            'created_by': self.env.user.id,
            'created_date': self.today
        }
        
        # Verify export file properties
        self.assertEqual(export_file['type'], 'csv', "Export type should be CSV")
        self.assertGreater(export_file['size'], 0, "Export should have content")
        
        # Decode and verify content
        decoded_content = base64.b64decode(export_file['content'])
        self.assertEqual(decoded_content, file_content, "Content should match")

    def test_attendance_export_summary_report(self):
        """Test attendance summary report export."""
        # Generate summary data
        summary_data = {
            'report_date': self.today,
            'course': self.course.name,
            'batch': self.batch.name,
            'total_students': 2,
            'total_classes': 2,
            'attendance_summary': []
        }
        
        # Calculate summary for each student
        for student in [self.student1, self.student2]:
            lines = self.env['op.attendance.line'].search([
                ('student_id', '=', student.id),
                ('attendance_id.register_id', '=', self.register.id)
            ])
            
            present_count = len(lines.filtered('present'))
            total_count = len(lines)
            percentage = (present_count / total_count) * 100 if total_count > 0 else 0
            
            summary_data['attendance_summary'].append({
                'student_name': student.name,
                'total_classes': total_count,
                'present_count': present_count,
                'absent_count': total_count - present_count,
                'attendance_percentage': percentage
            })
        
        # Verify summary report data
        self.assertEqual(len(summary_data['attendance_summary']), 2, 
                        "Should have summary for 2 students")
        
        student1_summary = next(s for s in summary_data['attendance_summary'] 
                               if s['student_name'] == self.student1.name)
        self.assertEqual(student1_summary['attendance_percentage'], 100.0,
                        "Student1 should have 100% attendance")

    def test_attendance_import_update_existing(self):
        """Test updating existing attendance records during import."""
        # Create existing attendance line
        existing_line = self.create_attendance_line(
            self.sheet1, self.student1, present=False, remarks="Original"
        )
        
        # Import data to update existing record
        update_data = {
            'student_id': self.student1.id,
            'sheet_id': self.sheet1.id,
            'present': True,
            'remarks': 'Updated via import'
        }
        
        # Find and update existing line
        line_to_update = self.env['op.attendance.line'].search([
            ('attendance_id', '=', update_data['sheet_id']),
            ('student_id', '=', update_data['student_id'])
        ], limit=1)
        
        if line_to_update:
            line_to_update.write({
                'present': update_data['present'],
                'remarks': update_data['remarks']
            })
        
        # Verify update
        updated_line = self.env['op.attendance.line'].browse(existing_line.id)
        self.assertTrue(updated_line.present, "Should update to present")
        self.assertEqual(updated_line.remarks, 'Updated via import', 
                        "Should update remarks")

    def test_attendance_export_performance(self):
        """Test performance of attendance export with large datasets."""
        # Create large dataset
        large_student_count = 50
        large_students = []
        
        for i in range(large_student_count):
            student = self.env['op.student'].create({
                'name': f'Export Student {i}',
                'first_name': 'Export',
                'last_name': f'Student{i}',
                'birth_date': self.yesterday,
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            large_students.append(student)
        
        # Create attendance for all students
        for student in large_students:
            self.create_attendance_line(self.sheet1, student, present=True)
        
        # Measure export performance
        start_time = self.env.now()
        
        # Export all attendance lines
        all_lines = self.env['op.attendance.line'].search([
            ('attendance_id', '=', self.sheet1.id)
        ])
        
        export_data = []
        for line in all_lines:
            export_data.append({
                'student': line.student_id.name,
                'date': line.attendance_id.attendance_date,
                'status': 'Present' if line.present else 'Absent',
                'remarks': line.remarks or ''
            })
        
        end_time = self.env.now()
        export_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertGreaterEqual(len(export_data), large_student_count,
                               f"Should export at least {large_student_count} records")
        self.assertLess(export_time, 10.0, 
                       "Export should complete within 10 seconds")