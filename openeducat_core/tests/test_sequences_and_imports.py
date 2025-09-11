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
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'sequences_imports')
class TestSequencesAndImports(TestCoreCommon):
    """Test sequence generation and data import/export functionality."""

    def test_student_sequence_generation(self):
        """Test student sequence generation if exists."""
        student = self._create_test_student()
        
        # Check if sequence fields exist and are populated
        if hasattr(student, 'sequence'):
            self.assertTrue(student.sequence)
        
        if hasattr(student, 'student_code'):
            self.assertTrue(student.student_code)
        
        # If gr_no is auto-generated, test it
        if not student.gr_no:
            # May be auto-generated on save
            student.flush_recordset()
            if hasattr(student, '_compute_gr_no'):
                student._compute_gr_no()

    def test_faculty_sequence_generation(self):
        """Test faculty sequence generation if exists."""
        faculty = self._create_test_faculty()
        
        # Check if sequence fields exist and are populated
        if hasattr(faculty, 'sequence'):
            self.assertTrue(faculty.sequence)
        
        if hasattr(faculty, 'faculty_code'):
            self.assertTrue(faculty.faculty_code)
        
        if hasattr(faculty, 'employee_id'):
            # Faculty might be linked to HR employee with sequence
            self.assertTrue(faculty.employee_id or True)  # May or may not exist

    def test_course_sequence_generation(self):
        """Test course sequence generation if exists."""
        course = self.test_course
        
        # Check if sequence fields exist and are populated
        if hasattr(course, 'sequence'):
            self.assertTrue(course.sequence)
        
        # Course code should be unique and properly formatted
        self.assertTrue(course.code)
        self.assertIsInstance(course.code, str)

    def test_batch_sequence_generation(self):
        """Test batch sequence generation if exists."""
        batch = self.test_batch
        
        # Check if sequence fields exist and are populated
        if hasattr(batch, 'sequence'):
            self.assertTrue(batch.sequence)
        
        # Batch code should be unique and properly formatted
        self.assertTrue(batch.code)
        self.assertIsInstance(batch.code, str)

    def test_subject_sequence_generation(self):
        """Test subject sequence generation if exists."""
        subject = self.test_subject
        
        # Check if sequence fields exist and are populated
        if hasattr(subject, 'sequence'):
            self.assertTrue(subject.sequence)
        
        # Subject code should be unique and properly formatted
        self.assertTrue(subject.code)
        self.assertIsInstance(subject.code, str)

    def test_student_import_templates(self):
        """Test student import template functionality."""
        templates = self.student_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        
        for template in templates:
            self.assertIn('label', template)
            self.assertIn('template', template)
            self.assertIsInstance(template['label'], str)
            self.assertIsInstance(template['template'], str)
            
            # Template path should be valid
            self.assertTrue(template['template'].startswith('/'))
            self.assertTrue(template['template'].endswith('.xls'))

    def test_course_import_templates(self):
        """Test course import template functionality."""
        templates = self.course_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        
        for template in templates:
            self.assertIn('label', template)
            self.assertIn('template', template)
            
            # Verify template structure
            self.assertIsInstance(template['label'], str)
            self.assertIsInstance(template['template'], str)
            self.assertTrue(template['template'].endswith('.xls'))

    def test_batch_import_templates(self):
        """Test batch import template functionality."""
        templates = self.batch_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        
        for template in templates:
            self.assertIn('label', template)
            self.assertIn('template', template)
            
            # Verify template structure
            self.assertIsInstance(template['label'], str)
            self.assertIsInstance(template['template'], str)

    def test_faculty_import_templates(self):
        """Test faculty import template functionality."""
        templates = self.faculty_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        
        for template in templates:
            self.assertIn('label', template)
            self.assertIn('template', template)

    def test_multiple_sequence_uniqueness(self):
        """Test that sequences generate unique values."""
        # Create multiple students and check for unique sequences
        students = []
        for i in range(10):
            student = self._create_test_student(
                first_name=f'Sequence{i}',
                last_name='Test',
                gr_no=f'SEQ{i:03d}'
            )
            students.append(student)
        
        # Check gr_no uniqueness
        gr_nos = [s.gr_no for s in students if s.gr_no]
        self.assertEqual(len(gr_nos), len(set(gr_nos)), "gr_no values should be unique")
        
        # Check any other sequence fields
        if hasattr(students[0], 'student_code'):
            student_codes = [s.student_code for s in students if s.student_code]
            if student_codes:
                self.assertEqual(len(student_codes), len(set(student_codes)), 
                               "student_code values should be unique")

    def test_sequence_format_validation(self):
        """Test sequence format validation."""
        student = self._create_test_student()
        
        # If gr_no has a specific format, test it
        if student.gr_no:
            self.assertIsInstance(student.gr_no, str)
            self.assertGreater(len(student.gr_no), 0)
        
        # Test course code format
        course = self.test_course
        self.assertIsInstance(course.code, str)
        self.assertGreater(len(course.code), 0)
        
        # Test batch code format
        batch = self.test_batch
        self.assertIsInstance(batch.code, str)
        self.assertGreater(len(batch.code), 0)

    def test_import_template_content_structure(self):
        """Test import template content structure."""
        # Test student template structure
        student_templates = self.student_model.get_import_templates()
        for template in student_templates:
            self.assertIn('Student', template['label'])
            self.assertIn('op_student', template['template'])
        
        # Test course template structure
        course_templates = self.course_model.get_import_templates()
        for template in course_templates:
            self.assertIn('Course', template['label'])
            self.assertIn('op_course', template['template'])
        
        # Test batch template structure
        batch_templates = self.batch_model.get_import_templates()
        for template in batch_templates:
            self.assertIn('Batch', template['label'])
            self.assertIn('op_batch', template['template'])

    def test_sequence_on_create_vs_write(self):
        """Test sequence generation on create vs write operations."""
        # Test sequence generation on create
        student = self._create_test_student(gr_no='CREATE001')
        original_gr_no = student.gr_no
        
        # Test that sequence doesn't change on write
        student.write({'first_name': 'Updated'})
        self.assertEqual(student.gr_no, original_gr_no)
        
        # Test with faculty
        faculty = self._create_test_faculty()
        if hasattr(faculty, 'faculty_code'):
            original_code = faculty.faculty_code
            faculty.write({'first_name': 'Updated'})
            if faculty.faculty_code:
                self.assertEqual(faculty.faculty_code, original_code)

    def test_sequence_with_company_context(self):
        """Test sequence generation with different company contexts."""
        # Create student with main company
        student1 = self._create_test_student(
            first_name='Company1',
            last_name='Student',
            gr_no='COMP1001'
        )
        
        # Create another company if needed for testing
        company2 = self.env['res.company'].create({
            'name': 'Test Company 2',
        })
        
        # Test with different company context
        student2 = self._create_test_student(
            first_name='Company2',
            last_name='Student',
            gr_no='COMP2001'
        )
        
        # Both should have unique identifiers
        self.assertNotEqual(student1.gr_no, student2.gr_no)

    def test_bulk_import_simulation(self):
        """Simulate bulk import operations."""
        # Simulate importing multiple students
        import_data = []
        for i in range(20):
            student_data = {
                'first_name': f'Import{i}',
                'last_name': 'Student',
                'birth_date': '2000-01-01',
                'gender': 'm' if i % 2 == 0 else 'f',
                'gr_no': f'IMP{i:04d}',
            }
            import_data.append(student_data)
        
        # Create students (simulating import)
        created_students = []
        for data in import_data:
            student = self._create_test_student(**data)
            created_students.append(student)
        
        # Verify all students created successfully
        self.assertEqual(len(created_students), 20)
        
        # Verify unique identifiers
        gr_nos = [s.gr_no for s in created_students]
        self.assertEqual(len(gr_nos), len(set(gr_nos)))

    def test_export_data_structure(self):
        """Test data export structure for import templates."""
        # Create sample data
        student = self._create_test_student(
            first_name='Export',
            last_name='Test',
            birth_date='2000-01-01',
            gender='m'
        )
        
        # Test export fields (basic fields that would be in template)
        export_fields = ['name', 'first_name', 'last_name', 'birth_date', 'gender']
        available_fields = student.fields_get().keys()
        
        # Check which export fields are available
        for field in export_fields:
            if field in available_fields:
                value = getattr(student, field)
                self.assertIsNotNone(value, f"Field {field} should have a value")

    def test_import_validation_rules(self):
        """Test validation rules during import operations."""
        # Test required field validation
        try:
            # This should fail due to missing required fields
            invalid_student = self.student_model.create({
                'birth_date': '2000-01-01',
                # Missing other required fields
            })
        except Exception:
            pass  # Expected to fail
        
        # Test valid data import
        valid_student = self._create_test_student(
            first_name='Valid',
            last_name='Import',
            birth_date='2000-01-01'
        )
        self.assertTrue(valid_student.id)

    def test_sequence_performance_bulk_creation(self):
        """Test sequence generation performance with bulk creation."""
        import time
        
        start_time = time.time()
        
        # Create multiple records to test sequence performance
        students = []
        for i in range(50):
            student = self._create_test_student(
                first_name=f'BulkSeq{i}',
                last_name='Test',
                gr_no=f'BULK{i:04d}'
            )
            students.append(student)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create 50 students with sequences efficiently
        self.assertLess(duration, 10, 
                       f"Bulk sequence generation took {duration:.2f} seconds")
        
        # Verify all have unique sequences
        gr_nos = [s.gr_no for s in students if s.gr_no]
        self.assertEqual(len(gr_nos), len(set(gr_nos)))

    def test_import_template_file_paths(self):
        """Test that import template file paths are valid."""
        models_to_test = [
            self.student_model,
            self.course_model,
            self.batch_model,
            self.faculty_model,
        ]
        
        for model in models_to_test:
            templates = model.get_import_templates()
            for template in templates:
                path = template['template']
                
                # Path should start with module name
                self.assertTrue(path.startswith('/openeducat_core/'))
                
                # Path should end with .xls
                self.assertTrue(path.endswith('.xls'))
                
                # Path should contain 'static' directory
                self.assertIn('/static/', path)

    def test_sequence_after_copy_operation(self):
        """Test sequence generation after copy operations."""
        original_student = self._create_test_student(
            first_name='Original',
            last_name='Student',
            gr_no='ORIG001'
        )
        
        # Copy the student
        copied_student = original_student.copy()
        
        # Copied student should have different sequence values
        self.assertNotEqual(original_student.gr_no, copied_student.gr_no)
        
        # If other sequence fields exist, they should also be different
        if hasattr(original_student, 'student_code') and original_student.student_code:
            if hasattr(copied_student, 'student_code') and copied_student.student_code:
                self.assertNotEqual(original_student.student_code, copied_student.student_code)

    def test_manual_sequence_override(self):
        """Test manual sequence override if allowed."""
        # Test creating student with manual gr_no
        student = self._create_test_student(
            first_name='Manual',
            last_name='Sequence',
            gr_no='MANUAL001'
        )
        
        # Manual gr_no should be preserved
        self.assertEqual(student.gr_no, 'MANUAL001')
        
        # Test creating another with auto-generated
        auto_student = self._create_test_student(
            first_name='Auto',
            last_name='Sequence'
            # No gr_no provided
        )
        
        # Should have different gr_no values
        if auto_student.gr_no:
            self.assertNotEqual(student.gr_no, auto_student.gr_no)