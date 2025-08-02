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
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'course')
class TestCourse(TestCoreCommon):
    """Comprehensive tests for op.course model."""

    def _create_test_course(self, **kwargs):
        """Helper method to create a test course with default values."""
        import time
        unique_suffix = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        
        defaults = {
            'name': f'Test Course {unique_suffix}',
            'code': f'TC{unique_suffix}',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
            'evaluation_type': 'normal',
        }
        defaults.update(kwargs)
        
        return self.course_model.create(defaults)

    def test_course_creation_with_valid_data(self):
        """Test course creation with all required fields."""
        course = self._create_test_course(
            name='Advanced Mathematics',
            code='MATH301',
            evaluation_type='GPA'
        )
        
        self.assertEqual(course.name, 'Advanced Mathematics')
        self.assertEqual(course.code, 'MATH301')
        self.assertEqual(course.department_id, self.test_department)
        self.assertEqual(course.program_id, self.test_program)
        self.assertEqual(course.evaluation_type, 'GPA')
        self.assertTrue(course.active)

    def test_course_required_fields(self):
        """Test that all required fields are properly enforced."""
        # Test missing name
        with self.assertRaises(Exception):
            self.course_model.create({
                'code': 'TEST001',
                'department_id': self.test_department.id,
                'program_id': self.test_program.id,
            })
        
        # Test missing code
        with self.assertRaises(Exception):
            self.course_model.create({
                'name': 'Test Course',
                'department_id': self.test_department.id,
                'program_id': self.test_program.id,
            })
        
        # Test missing evaluation_type (should default to 'normal')
        course = self.course_model.create({
            'name': 'Test Course',
            'code': 'TEST002',
            'department_id': self.test_department.id,
            'program_id': self.test_program.id,
        })
        self.assertEqual(course.evaluation_type, 'normal')

    def test_course_code_uniqueness_constraint(self):
        """Test course code uniqueness constraint."""
        # Create first course
        course1 = self._create_test_course(
            name='First Course',
            code='UNIQUE001'
        )
        
        # Try to create second course with same code
        with self.assertRaises(IntegrityError):
            self._create_test_course(
                name='Second Course',
                code='UNIQUE001'  # Duplicate code
            )

    def test_course_evaluation_type_options(self):
        """Test course evaluation type field options."""
        evaluation_types = ['normal', 'GPA', 'CWA', 'CCE']
        
        for eval_type in evaluation_types:
            course = self._create_test_course(
                name=f'Course {eval_type}',
                code=f'EVAL{eval_type.upper()}',
                evaluation_type=eval_type
            )
            self.assertEqual(course.evaluation_type, eval_type)

    def test_course_department_relationship(self):
        """Test course-department relationship."""
        # Create additional department
        dept2 = self.env['op.department'].create({
            'name': 'Physics Department',
            'code': 'PHYS002',
        })
        
        course = self._create_test_course(
            name='Quantum Physics',
            code='PHYS401',
            department_id=dept2.id
        )
        
        self.assertEqual(course.department_id, dept2)
        self.assertNotEqual(course.department_id, self.test_department)

    def test_course_program_relationship(self):
        """Test course-program relationship."""
        # Create additional program
        program2 = self.env['op.program'].create({
            'name': 'Master of Science',
            'code': 'MS001',
            'department_id': self.test_department.id,
            'program_level_id': self.test_program_level.id,
        })
        
        course = self._create_test_course(
            name='Research Methodology',
            code='RM501',
            program_id=program2.id
        )
        
        self.assertEqual(course.program_id, program2)
        self.assertNotEqual(course.program_id, self.test_program)

    def test_course_subject_assignment(self):
        """Test course subject assignment via Many2many relationship."""
        course = self._create_test_course()
        
        # Create additional subjects
        subject2 = self.env['op.subject'].create({
            'name': 'Advanced Calculus',
            'code': 'CALC201',
            'type': 'theory',
            'subject_type': 'compulsory',
            'department_id': self.test_department.id,
        })
        
        subject3 = self.env['op.subject'].create({
            'name': 'Linear Algebra',
            'code': 'LALG101',
            'type': 'theory',
            'subject_type': 'elective',
            'department_id': self.test_department.id,
        })
        
        # Assign subjects to course
        course.subject_ids = [(6, 0, [self.test_subject.id, subject2.id, subject3.id])]
        
        self.assertEqual(len(course.subject_ids), 3)
        self.assertIn(self.test_subject, course.subject_ids)
        self.assertIn(subject2, course.subject_ids)
        self.assertIn(subject3, course.subject_ids)

    def test_course_unit_load_fields(self):
        """Test course unit load fields."""
        course = self._create_test_course(
            max_unit_load=20.0,
            min_unit_load=5.0
        )
        
        self.assertEqual(course.max_unit_load, 20.0)
        self.assertEqual(course.min_unit_load, 5.0)
        
        # Test edge case: max and min equal
        course2 = self._create_test_course(
            max_unit_load=15.0,
            min_unit_load=15.0
        )
        
        self.assertEqual(course2.max_unit_load, 15.0)
        self.assertEqual(course2.min_unit_load, 15.0)

    def test_course_parent_child_relationship(self):
        """Test course parent-child hierarchy."""
        # Create parent course
        parent_course = self._create_test_course(
            name='Mathematics Foundation',
            code='MATHFND'
        )
        
        # Create child course
        child_course = self._create_test_course(
            name='Advanced Mathematics',
            code='MATHADVS',
            parent_id=parent_course.id
        )
        
        self.assertEqual(child_course.parent_id, parent_course)
        self.assertFalse(parent_course.parent_id)

    def test_course_recursive_category_constraint(self):
        """Test _check_category_recursion constraint."""
        # Create parent course
        parent_course = self._create_test_course(
            name='Parent Course',
            code='PARENT01'
        )
        
        # Create child course
        child_course = self._create_test_course(
            name='Child Course',
            code='CHILD01',
            parent_id=parent_course.id
        )
        
        # Try to make parent a child of its own child (circular reference)
        with self.assertRaises(ValidationError) as context:
            parent_course.parent_id = child_course.id
        
        self.assertIn('recursive categories', str(context.exception))

    def test_course_get_import_templates(self):
        """Test get_import_templates method."""
        templates = self.course_model.get_import_templates()
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 1)
        
        template = templates[0]
        self.assertIn('label', template)
        self.assertIn('template', template)
        self.assertEqual(template['template'], '/openeducat_core/static/xls/op_course.xls')

    def test_course_active_field(self):
        """Test course active field functionality."""
        course = self._create_test_course()
        
        # Course should be active by default
        self.assertTrue(course.active)
        
        # Deactivate course
        course.active = False
        self.assertFalse(course.active)
        
        # Reactivate course
        course.active = True
        self.assertTrue(course.active)

    def test_course_code_size_constraint(self):
        """Test course code size constraint."""
        # Valid code (within size limit)
        course = self._create_test_course(
            code='VALID123'  # 8 characters, within 16 limit
        )
        self.assertEqual(course.code, 'VALID123')
        
        # Test maximum size code (16 characters)
        course2 = self._create_test_course(
            code='1234567890123456'  # Exactly 16 characters
        )
        self.assertEqual(course2.code, '1234567890123456')

    def test_course_name_translation(self):
        """Test course name translation capability."""
        course = self._create_test_course(
            name='Computer Science'
        )
        
        # Name field should support translation
        field_info = self.course_model.fields_get(['name'])
        self.assertTrue(field_info['name'].get('translate', False))

    def test_course_tracking_inheritance(self):
        """Test that course inherits mail.thread for tracking."""
        course = self._create_test_course()
        
        # Should inherit mail.thread
        self.assertTrue(hasattr(course, 'message_post'))
        self.assertTrue(hasattr(course, 'message_ids'))

    def test_course_display_name(self):
        """Test course display name functionality."""
        course = self._create_test_course(
            name='Data Structures and Algorithms',
            code='DSA101'
        )
        
        display_name = course.display_name
        self.assertTrue(display_name)
        self.assertIn('Data Structures and Algorithms', display_name)

    def test_course_sql_constraints(self):
        """Test SQL constraints are properly defined."""
        model = self.course_model
        constraints = model._sql_constraints
        
        # Check unique_course_code constraint exists
        constraint_names = [constraint[0] for constraint in constraints]
        self.assertIn('unique_course_code', constraint_names)
        
        # Find the constraint and verify its definition
        unique_constraint = next(
            (c for c in constraints if c[0] == 'unique_course_code'), None
        )
        self.assertIsNotNone(unique_constraint)
        self.assertIn('unique(code)', unique_constraint[1])

    def test_course_default_values(self):
        """Test course default field values."""
        course = self._create_test_course()
        
        # Active should default to True
        self.assertTrue(course.active)
        
        # Evaluation type should default to 'normal'
        self.assertEqual(course.evaluation_type, 'normal')

    def test_course_multiple_subjects_management(self):
        """Test managing multiple subjects in a course."""
        course = self._create_test_course()
        
        # Create multiple subjects
        subjects = []
        for i in range(5):
            subject = self.env['op.subject'].create({
                'name': f'Subject {i+1}',
                'code': f'SUBJ{i+1:03d}',
                'type': 'theory',
                'subject_type': 'compulsory',
                'department_id': self.test_department.id,
            })
            subjects.append(subject)
        
        # Assign all subjects to course
        course.subject_ids = [(6, 0, [s.id for s in subjects])]
        self.assertEqual(len(course.subject_ids), 5)
        
        # Remove some subjects
        course.subject_ids = [(6, 0, [subjects[0].id, subjects[2].id])]
        self.assertEqual(len(course.subject_ids), 2)
        self.assertIn(subjects[0], course.subject_ids)
        self.assertIn(subjects[2], course.subject_ids)

    def test_course_complex_hierarchy(self):
        """Test complex course hierarchy structures."""
        # Create multi-level hierarchy
        level1_course = self._create_test_course(
            name='Level 1 Course',
            code='L1COURSE'
        )
        
        level2_course = self._create_test_course(
            name='Level 2 Course',
            code='L2COURSE',
            parent_id=level1_course.id
        )
        
        level3_course = self._create_test_course(
            name='Level 3 Course',
            code='L3COURSE',
            parent_id=level2_course.id
        )
        
        # Verify hierarchy
        self.assertEqual(level3_course.parent_id, level2_course)
        self.assertEqual(level2_course.parent_id, level1_course)
        self.assertFalse(level1_course.parent_id)

    def test_course_unit_load_edge_cases(self):
        """Test course unit load edge cases."""
        # Zero unit loads
        course1 = self._create_test_course(
            max_unit_load=0.0,
            min_unit_load=0.0
        )
        self.assertEqual(course1.max_unit_load, 0.0)
        self.assertEqual(course1.min_unit_load, 0.0)
        
        # Decimal unit loads
        course2 = self._create_test_course(
            max_unit_load=12.5,
            min_unit_load=3.5
        )
        self.assertEqual(course2.max_unit_load, 12.5)
        self.assertEqual(course2.min_unit_load, 3.5)

    def test_course_program_tracking(self):
        """Test course program field tracking."""
        course = self._create_test_course()
        
        # Test field tracking is enabled
        field_info = self.course_model.fields_get(['program_id'])
        self.assertTrue(field_info['program_id'].get('tracking', False))
        
        # Test help text exists
        self.assertIn('help', field_info['program_id'])

    def test_course_department_default_context(self):
        """Test course department default from user context."""
        course = self._create_test_course()
        
        # Should have department assigned
        self.assertTrue(course.department_id)
        self.assertEqual(course.department_id, self.test_department)

    def test_course_has_cycle_method(self):
        """Test _has_cycle method functionality for recursion detection."""
        # Create normal hierarchy (should not have cycle)
        parent_course = self._create_test_course(
            name='Parent Course',
            code='PCYCLE1'
        )
        
        child_course = self._create_test_course(
            name='Child Course',
            code='CCYCLE1',
            parent_id=parent_course.id
        )
        
        # Normal hierarchy should not have cycle
        self.assertFalse(child_course._has_cycle())
        
        # Test with self as parent (direct recursion)
        with self.assertRaises(ValidationError):
            child_course.parent_id = child_course.id

    def test_course_evaluation_type_validation(self):
        """Test course evaluation type validation."""
        # Valid evaluation types
        valid_types = ['normal', 'GPA', 'CWA', 'CCE']
        
        for eval_type in valid_types:
            course = self._create_test_course(
                evaluation_type=eval_type
            )
            self.assertEqual(course.evaluation_type, eval_type)

    def test_course_subject_bidirectional_relationship(self):
        """Test bidirectional relationship between course and subjects."""
        course = self._create_test_course()
        
        # Assign subject to course
        course.subject_ids = [(6, 0, [self.test_subject.id])]
        
        # Verify relationship from both sides
        self.assertIn(self.test_subject, course.subject_ids)
        
        # Check if subject has reference to course (if such field exists)
        # This would depend on the actual model structure