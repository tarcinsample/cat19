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

from datetime import date, timedelta
import uuid
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'batch')
class TestBatch(TestCoreCommon):
    """Comprehensive tests for op.batch model."""

    def _create_test_batch(self, **kwargs):
        """Helper method to create a test batch with default values."""
        import time
        # Use both timestamp and random UUID to ensure uniqueness
        unique_suffix = str(int(time.time() * 1000))[-6:] + str(uuid.uuid4())[:4]
        
        defaults = {
            'name': f'Test Batch {unique_suffix}',
            'code': f'TB{unique_suffix}',
            'course_id': self.test_course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
        }
        defaults.update(kwargs)
        
        return self.batch_model.create(defaults)

    def test_batch_creation_with_valid_data(self):
        """Test batch creation with all required fields."""
        batch = self._create_test_batch(
            name='Computer Science Batch 2024',
            code='CS2024',
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        self.assertEqual(batch.name, 'Computer Science Batch 2024')
        self.assertEqual(batch.code, 'CS2024')
        self.assertEqual(batch.course_id, self.test_course)
        self.assertEqual(str(batch.start_date), '2024-01-01')
        self.assertEqual(str(batch.end_date), '2024-12-31')
        self.assertTrue(batch.active)

    def test_batch_date_validation_valid_dates(self):
        """Test batch creation with valid start and end dates."""
        batch = self._create_test_batch(
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        self.assertTrue(batch.start_date)
        self.assertTrue(batch.end_date)
        self.assertLess(batch.start_date, batch.end_date)

    def test_batch_date_validation_invalid_dates(self):
        """Test batch creation with invalid dates (end before start)."""
        with self.assertRaises(ValidationError) as context:
            self._create_test_batch(
                start_date='2024-12-31',
                end_date='2024-01-01'  # End date before start date
            )
        
        self.assertIn('End Date cannot be set before Start Date', str(context.exception))

    def test_batch_code_uniqueness_constraint(self):
        """Test batch code uniqueness constraint."""
        # Create first batch
        batch1 = self._create_test_batch(
            name='First Batch',
            code='UNIQUE001'
        )
        
        # Try to create second batch with same code
        with self.assertRaises(IntegrityError):
            self._create_test_batch(
                name='Second Batch',
                code='UNIQUE001'  # Duplicate code
            )

    def test_batch_required_fields(self):
        """Test that all required fields are properly enforced."""
        # Test missing name
        with self.assertRaises(Exception):
            self.batch_model.create({
                'code': 'TEST001',
                'course_id': self.test_course.id,
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=30),
            })
        
        # Test missing code
        with self.assertRaises(Exception):
            self.batch_model.create({
                'name': 'Test Batch',
                'course_id': self.test_course.id,
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=30),
            })
        
        # Test missing course_id
        with self.assertRaises(Exception):
            self.batch_model.create({
                'name': 'Test Batch',
                'code': 'TEST001',
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=30),
            })

    def test_batch_course_relationship(self):
        """Test batch-course relationship."""
        batch = self._create_test_batch()
        
        self.assertEqual(batch.course_id, self.test_course)
        
        # Test with different course
        course2 = self.env['op.course'].create({
            'name': 'Advanced Mathematics',
            'code': 'MATH201',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        batch2 = self._create_test_batch(
            name='Math Batch',
            code='MB2024',
            course_id=course2.id
        )
        
        self.assertEqual(batch2.course_id, course2)
        self.assertNotEqual(batch2.course_id, self.test_course)

    def test_batch_active_field(self):
        """Test batch active field functionality."""
        batch = self._create_test_batch()
        
        # Batch should be active by default
        self.assertTrue(batch.active)
        
        # Deactivate batch
        batch.active = False
        self.assertFalse(batch.active)
        
        # Reactivate batch
        batch.active = True
        self.assertTrue(batch.active)

    def test_batch_get_import_templates(self):
        """Test get_import_templates method."""
        templates = self.batch_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 1)
        
        template = templates[0]
        self.assertIn('label', template)
        self.assertIn('template', template)
        self.assertEqual(template['template'], '/openeducat_core/static/xls/op_batch.xls')

    def test_batch_name_search_basic(self):
        """Test basic name_search functionality."""
        batch1 = self._create_test_batch(
            name='Computer Science Batch',
            code='CS2024'
        )
        batch2 = self._create_test_batch(
            name='Mathematics Batch',
            code='MATH2024'
        )
        
        # Search by name
        results = self.batch_model.name_search('Computer')
        batch_ids = [result[0] for result in results]
        self.assertIn(batch1.id, batch_ids)
        self.assertNotIn(batch2.id, batch_ids)
        
        # Search by code
        results = self.batch_model.name_search('MATH')
        batch_ids = [result[0] for result in results]
        self.assertIn(batch2.id, batch_ids)
        self.assertNotIn(batch1.id, batch_ids)

    def test_batch_name_search_with_parent_context(self):
        """Test name_search with get_parent_batch context."""
        # Create parent course
        parent_course = self.env['op.course'].create({
            'name': 'Parent Course',
            'code': 'PARENT001',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        # Create child course
        child_course = self.env['op.course'].create({
            'name': 'Child Course',
            'code': 'CHILD001',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'parent_id': parent_course.id,
        })
        
        # Create batches for both courses
        parent_batch = self._create_test_batch(
            name='Parent Batch',
            code='PB001',
            course_id=parent_course.id
        )
        child_batch = self._create_test_batch(
            name='Child Batch',
            code='CB001',
            course_id=child_course.id
        )
        
        # Search with parent context
        results = self.batch_model.with_context(
            get_parent_batch=True,
            course_id=child_course.id
        ).name_search('')
        
        batch_ids = [result[0] for result in results]
        self.assertIn(parent_batch.id, batch_ids)
        self.assertIn(child_batch.id, batch_ids)

    def test_batch_display_name(self):
        """Test batch display name functionality."""
        batch = self._create_test_batch(
            name='Display Test Batch',
            code='DTB2024_' + str(uuid.uuid4())[:4]
        )
        
        display_name = batch.display_name
        self.assertTrue(display_name)
        self.assertIn('Display Test Batch', display_name)

    def test_batch_default_values(self):
        """Test batch default field values."""
        batch = self._create_test_batch()
        
        # Active should default to True
        self.assertTrue(batch.active)
        
        # Start date should default to today
        self.assertEqual(batch.start_date, date.today())

    def test_batch_date_edge_cases(self):
        """Test batch date validation edge cases."""
        today = date.today()
        
        # Same start and end date should be valid
        batch = self._create_test_batch(
            start_date=today,
            end_date=today
        )
        self.assertEqual(batch.start_date, batch.end_date)
        
        # One day difference should be valid
        batch2 = self._create_test_batch(
            start_date=today,
            end_date=today + timedelta(days=1)
        )
        self.assertLess(batch2.start_date, batch2.end_date)

    def test_batch_sql_constraints(self):
        """Test SQL constraints are properly defined."""
        model = self.batch_model
        constraints = model._sql_constraints
        
        # Check unique_batch_code constraint exists
        constraint_names = [constraint[0] for constraint in constraints]
        self.assertIn('unique_batch_code', constraint_names)
        
        # Find the constraint and verify its definition
        unique_constraint = next(
            (c for c in constraints if c[0] == 'unique_batch_code'), None
        )
        self.assertIsNotNone(unique_constraint)
        self.assertIn('unique(code)', unique_constraint[1])

    def test_batch_tracking_inheritance(self):
        """Test that batch inherits mail.thread for tracking."""
        batch = self._create_test_batch()
        
        # Should inherit mail.thread
        self.assertTrue(hasattr(batch, 'message_post'))
        self.assertTrue(hasattr(batch, 'message_ids'))

    def test_batch_code_size_constraint(self):
        """Test batch code size constraint."""
        # Valid code (within size limit)
        batch = self._create_test_batch(
            code='VALID123'  # 8 characters, within 16 limit
        )
        self.assertEqual(batch.code, 'VALID123')
        
        # Test maximum size code (16 characters)
        batch2 = self._create_test_batch(
            code='1234567890123456'  # Exactly 16 characters
        )
        self.assertEqual(batch2.code, '1234567890123456')

    def test_batch_name_size_constraint(self):
        """Test batch name size constraint."""
        # Valid name (within size limit)
        batch = self._create_test_batch(
            name='Valid Batch Name'  # Within 32 character limit
        )
        self.assertEqual(batch.name, 'Valid Batch Name')
        
        # Test maximum size name (32 characters)
        max_name = 'A' * 32  # Exactly 32 characters
        batch2 = self._create_test_batch(
            name=max_name
        )
        self.assertEqual(batch2.name, max_name)

    def test_batch_multiple_courses(self):
        """Test batches can belong to different courses."""
        # Create additional courses
        course_math = self.env['op.course'].create({
            'name': 'Mathematics',
            'code': 'MATH101',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        course_physics = self.env['op.course'].create({
            'name': 'Physics',
            'code': 'PHYS101',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        
        # Create batches for different courses
        batch_cs = self._create_test_batch(
            name='CS Batch',
            code='CS001',
            course_id=self.test_course.id
        )
        batch_math = self._create_test_batch(
            name='Math Batch',
            code='MATH001',
            course_id=course_math.id
        )
        batch_physics = self._create_test_batch(
            name='Physics Batch',
            code='PHYS001',
            course_id=course_physics.id
        )
        
        self.assertEqual(batch_cs.course_id, self.test_course)
        self.assertEqual(batch_math.course_id, course_math)
        self.assertEqual(batch_physics.course_id, course_physics)

    def test_batch_date_validation_constraint_function(self):
        """Test the check_dates constraint function directly."""
        batch = self._create_test_batch(
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        # Valid dates should not raise exception
        try:
            batch.check_dates()
        except ValidationError:
            self.fail("check_dates() raised ValidationError with valid dates")
        
        # Invalid dates should raise exception
        batch.start_date = '2024-12-31'
        batch.end_date = '2024-01-01'
        
        with self.assertRaises(ValidationError):
            batch.check_dates()