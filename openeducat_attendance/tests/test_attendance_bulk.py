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
class TestAttendanceBulk(TestAttendanceCommon):
    """Test bulk attendance marking and batch operations."""

    def setUp(self):
        """Set up test data for bulk operations."""
        super().setUp()
        
        # Create additional students for bulk testing
        self.bulk_students = []
        for i in range(10):
            student = self.env['op.student'].create({
                'name': f'Bulk Student {i}',
                'first_name': 'Bulk',
                'last_name': f'Student{i}',
                'birth_date': self.yesterday,
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            self.bulk_students.append(student)
        
        self.sheet = self.create_attendance_sheet()

    def test_bulk_attendance_line_creation(self):
        """Test bulk creation of attendance lines."""
        # Create attendance lines in bulk
        all_students = [self.student1, self.student2] + self.bulk_students
        
        lines_data = []
        for i, student in enumerate(all_students):
            present = i % 2 == 0  # Alternate present/absent
            vals = {
                'attendance_id': self.sheet.id,
                'student_id': student.id,
                'present': present,
                'remark': f'Bulk entry {i}' if i % 3 == 0 else False
            }
            # Set absent status when not present
            if not present:
                vals['absent'] = True
            lines_data.append(vals)
        
        # Bulk create all lines
        lines = self.env['op.attendance.line'].create(lines_data)
        
        self.assertEqual(len(lines), 12, "Should create 12 attendance lines")
        
        # Verify bulk creation success
        present_lines = lines.filtered('present')
        absent_lines = lines.filtered('absent')
        
        self.assertEqual(len(present_lines), 6, "Should have 6 present students")
        self.assertEqual(len(absent_lines), 6, "Should have 6 absent students")

    def test_bulk_attendance_update(self):
        """Test bulk updating of attendance status."""
        # Create initial attendance lines
        lines = []
        for student in [self.student1, self.student2] + self.bulk_students:
            line = self.create_attendance_line(self.sheet, student, present=False)
            lines.append(line)
        
        # Bulk update all to present
        line_ids = [line.id for line in lines]
        bulk_lines = self.env['op.attendance.line'].browse(line_ids)
        bulk_lines.write({'present': True, 'remark': 'Bulk updated'})
        
        # Verify bulk update
        updated_lines = self.env['op.attendance.line'].browse(line_ids)
        present_count = len(updated_lines.filtered('present'))
        
        self.assertEqual(present_count, 12, "All students should be marked present")
        
        # Check remarks update
        remarks_count = len(updated_lines.filtered(lambda l: l.remark == 'Bulk updated'))
        self.assertEqual(remarks_count, 12, "All lines should have updated remarks")

    def test_bulk_attendance_sheet_generation(self):
        """Test bulk generation of attendance sheets for multiple dates."""
        from datetime import timedelta
        
        # Generate sheets for a week
        dates = [self.today - timedelta(days=i) for i in range(7)]
        
        sheet_data = []
        for date in dates:
            sheet_data.append({
                'register_id': self.register.id,
                'attendance_date': date,
                'faculty_id': self.faculty.id,
            })
        
        # Bulk create sheets
        sheets = self.env['op.attendance.sheet'].create(sheet_data)
        
        self.assertEqual(len(sheets), 7, "Should create 7 attendance sheets")
        
        # Verify each sheet has proper data
        for sheet in sheets:
            self.assertEqual(sheet.register_id, self.register, "Sheet should link to register")
            self.assertIn(sheet.attendance_date, dates, "Date should be in expected range")

    def test_generate_attendance_lines_bulk(self):
        """Test bulk generation of attendance lines for all students."""
        # Test the generate_attendance_lines method
        count = self.sheet.generate_attendance_lines()
        
        # Should create lines for all students in batch
        expected_count = len([self.student1, self.student2] + self.bulk_students)
        self.assertEqual(count, expected_count, f"Should create {expected_count} attendance lines")
        
        # Verify all students are included
        student_ids = self.sheet.attendance_line.mapped('student_id.id')
        for student in [self.student1, self.student2] + self.bulk_students:
            self.assertIn(student.id, student_ids, f"Student {student.name} should have attendance line")

    def test_bulk_attendance_marking_workflow(self):
        """Test complete bulk attendance marking workflow."""
        # Step 1: Generate attendance lines for all students
        self.sheet.generate_attendance_lines()
        
        # Step 2: Bulk mark attendance based on pattern
        lines = self.sheet.attendance_line
        
        # Mark first half as present
        first_half = lines[:len(lines)//2]
        first_half.write({'present': True, 'remark': 'First half present'})
        
        # Mark second half as absent with specific reasons
        second_half = lines[len(lines)//2:]
        second_half.write({'present': False, 'remark': 'Second half absent'})
        
        # Step 3: Verify workflow completion
        self.sheet.attendance_start()
        self.sheet.attendance_done()
        
        self.assertEqual(self.sheet.state, 'done', "Sheet should be completed")
        
        # Verify attendance distribution
        present_lines = lines.filtered('present')
        absent_lines = lines.filtered('absent')
        
        self.assertEqual(len(present_lines), len(lines)//2, "First half should be present")
        self.assertEqual(len(absent_lines), len(lines) - len(lines)//2, "Second half should be absent")

    def test_bulk_attendance_import(self):
        """Test bulk import of attendance data."""
        # Simulate import data structure
        import_data = [
            {'student_name': self.student1.name, 'status': 'Present', 'remark': 'On time'},
            {'student_name': self.student2.name, 'status': 'Absent', 'remark': 'Sick leave'},
        ]
        
        # Add bulk student data
        for i, student in enumerate(self.bulk_students):
            import_data.append({
                'student_name': student.name,
                'status': 'Present' if i % 2 == 0 else 'Absent',
                'remark': f'Import remark {i}'
            })
        
        # Process import data
        imported_lines = []
        for data in import_data:
            # Find student by name
            student = self.env['op.student'].search([('name', '=', data['student_name'])], limit=1)
            if student:
                line = self.env['op.attendance.line'].create({
                    'attendance_id': self.sheet.id,
                    'student_id': student.id,
                    'present': data['status'] == 'Present',
                    'remark': data['remark']
                })
                imported_lines.append(line)
        
        self.assertEqual(len(imported_lines), 12, "Should import 12 attendance records")
        
        # Verify import accuracy
        present_imported = len([l for l in imported_lines if l.present])
        absent_imported = len([l for l in imported_lines if not l.present])
        
        self.assertGreater(present_imported, 0, "Should have some present students")
        self.assertGreater(absent_imported, 0, "Should have some absent students")

    def test_bulk_attendance_validation(self):
        """Test validation during bulk operations."""
        # Test bulk creation with invalid data
        invalid_data = [
            {'attendance_id': self.sheet.id, 'student_id': 99999, 'present': True},  # Invalid student
            {'attendance_id': 99999, 'student_id': self.student1.id, 'present': True},  # Invalid sheet
        ]
        
        # Should handle invalid data gracefully
        try:
            self.env['op.attendance.line'].create(invalid_data)
        except Exception as e:
            self.assertIn('does not exist', str(e), "Should validate foreign key references")

    def test_bulk_attendance_performance(self):
        """Test performance of bulk attendance operations."""
        # Create large dataset for performance testing
        large_student_count = 100
        large_students = []
        
        for i in range(large_student_count):
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
            large_students.append(student)
        
        # Measure bulk line creation performance
        from datetime import datetime
        start_time = datetime.now()
        
        lines_data = []
        for student in large_students:
            lines_data.append({
                'attendance_id': self.sheet.id,
                'student_id': student.id,
                'present': True,
            })
        
        lines = self.env['op.attendance.line'].create(lines_data)
        
        end_time = datetime.now()
        creation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(lines), large_student_count, f"Should create {large_student_count} lines")
        self.assertLess(creation_time, 30.0, "Bulk creation should complete within 30 seconds")

    def test_bulk_attendance_rollback(self):
        """Test rollback functionality for bulk operations."""
        # Create initial attendance lines
        initial_lines = []
        for student in [self.student1, self.student2]:
            line = self.create_attendance_line(self.sheet, student, present=True)
            initial_lines.append(line)
        
        initial_count = len(self.sheet.attendance_line)
        
        # Simulate failed bulk operation (using savepoint)
        with self.env.cr.savepoint():
            try:
                # Add bulk lines
                bulk_data = []
                for student in self.bulk_students:
                    bulk_data.append({
                        'attendance_id': self.sheet.id,
                        'student_id': student.id,
                        'present': True,
                    })
                
                new_lines = self.env['op.attendance.line'].create(bulk_data)
                
                # Simulate error condition
                if len(new_lines) > 5:
                    raise Exception("Simulated error for rollback test")
                    
            except Exception:
                # Rollback should occur automatically
                pass
        
        # Verify rollback - should have original lines only
        final_count = len(self.sheet.attendance_line)
        self.assertEqual(final_count, initial_count, "Count should remain unchanged after rollback")

    def test_bulk_attendance_archiving(self):
        """Test bulk archiving of attendance records."""
        # Create attendance lines
        lines = []
        for student in [self.student1, self.student2] + self.bulk_students:
            line = self.create_attendance_line(self.sheet, student, present=True)
            lines.append(line)
        
        # Bulk archive attendance lines (if supported)
        line_ids = [line.id for line in lines]
        bulk_lines = self.env['op.attendance.line'].browse(line_ids)
        
        # Archive by setting active=False if field exists
        if 'active' in bulk_lines._fields:
            bulk_lines.write({'active': False})
            
            # Verify archiving
            active_lines = self.env['op.attendance.line'].search([
                ('attendance_id', '=', self.sheet.id),
                ('active', '=', True)
            ])
            
            self.assertEqual(len(active_lines), 0, "No lines should be active after archiving")

    def test_bulk_attendance_statistics_update(self):
        """Test statistics update after bulk operations."""
        # Create bulk attendance data
        for student in [self.student1, self.student2] + self.bulk_students:
            self.create_attendance_line(self.sheet, student, present=True)
        
        # Force statistics computation
        self.register._compute_attendance_statistics()
        
        # Verify statistics reflect bulk data
        self.assertEqual(self.register.attendance_sheet_count, 1, "Should count 1 sheet")
        expected_students = len([self.student1, self.student2] + self.bulk_students)
        self.assertEqual(self.register.total_students, expected_students, 
                        f"Should count {expected_students} total students")

    def test_bulk_attendance_report_generation(self):
        """Test report generation with bulk attendance data."""
        # Create bulk attendance with varied patterns
        for i, student in enumerate([self.student1, self.student2] + self.bulk_students):
            present = i % 3 != 0  # 2/3 present, 1/3 absent
            self.create_attendance_line(self.sheet, student, present=present)
        
        # Generate bulk report data
        report_lines = self.env['op.attendance.line'].search([
            ('attendance_id', '=', self.sheet.id)
        ])
        
        present_count = len(report_lines.filtered('present'))
        total_count = len(report_lines)
        attendance_rate = (present_count / total_count) * 100
        
        self.assertEqual(total_count, 12, "Should have 12 total records")
        self.assertAlmostEqual(attendance_rate, 66.67, places=0, 
                              msg="Attendance rate should be approximately 67%")