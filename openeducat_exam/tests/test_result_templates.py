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

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_exam_common import TestExamCommon


@tagged('post_install', '-at_install', 'openeducat_exam')
class TestResultTemplates(TestExamCommon):
    """Test result template and grading system validation."""

    def test_grade_configuration_creation(self):
        """Test basic grade configuration creation."""
        grade_config = self.env['op.grade.configuration'].create({
            'name': 'Test Grading System',
            'result_line': [(0, 0, {
                'name': 'A',
                'marks_range_from': 80,
                'marks_range_to': 100,
                'grade': 'A',
            })],
        })
        
        self.assertEqual(grade_config.name, 'Test Grading System',
                        "Grade config name should be set")
        self.assertEqual(len(grade_config.result_line), 1,
                        "Should have 1 grade line")

    def test_result_line_creation(self):
        """Test creation of result lines in grade configuration."""
        result_line = self.env['op.result.line'].create({
            'name': 'Grade A',
            'marks_range_from': 80,
            'marks_range_to': 100,
            'grade': 'A',
            'grade_configuration_id': self.grade_config.id,
        })
        
        self.assertEqual(result_line.name, 'Grade A', "Result line name should be set")
        self.assertEqual(result_line.marks_range_from, 80, "From range should be 80")
        self.assertEqual(result_line.marks_range_to, 100, "To range should be 100")
        self.assertEqual(result_line.grade, 'A', "Grade should be A")

    def test_result_line_range_validation(self):
        """Test validation of marks range in result lines."""
        # Test invalid range (from > to)
        with self.assertRaises(ValidationError):
            self.env['op.result.line'].create({
                'name': 'Invalid Range',
                'marks_range_from': 90,
                'marks_range_to': 80,  # Invalid: to < from
                'grade': 'A',
                'grade_configuration_id': self.grade_config.id,
            })

    def test_result_line_negative_marks_validation(self):
        """Test validation for negative marks ranges."""
        # Test negative from range
        with self.assertRaises(ValidationError):
            self.env['op.result.line'].create({
                'name': 'Negative From',
                'marks_range_from': -10,  # Invalid: negative
                'marks_range_to': 50,
                'grade': 'F',
                'grade_configuration_id': self.grade_config.id,
            })

    def test_result_line_overlapping_ranges_validation(self):
        """Test validation for overlapping marks ranges."""
        # Create first result line
        self.env['op.result.line'].create({
            'name': 'Grade A',
            'marks_range_from': 80,
            'marks_range_to': 100,
            'grade': 'A',
            'grade_configuration_id': self.grade_config.id,
        })
        
        # Try to create overlapping range
        with self.assertRaises(ValidationError):
            self.env['op.result.line'].create({
                'name': 'Grade B',
                'marks_range_from': 75,
                'marks_range_to': 85,  # Overlaps with A grade
                'grade': 'B',
                'grade_configuration_id': self.grade_config.id,
            })

    def test_grade_calculation_from_marks(self):
        """Test grade calculation based on marks and grade configuration."""
        # Test different marks against grade configuration
        test_cases = [
            (95, 'A+'),  # 90-100
            (85, 'A'),   # 80-89
            (75, 'B'),   # 70-79
            (65, 'C'),   # 60-69
            (45, 'F'),   # 0-59
        ]
        
        for marks, expected_grade in test_cases:
            with self.subTest(marks=marks, expected_grade=expected_grade):
                calculated_grade = self._get_grade_for_marks(marks, self.grade_config)
                self.assertEqual(calculated_grade, expected_grade,
                               f"Marks {marks} should give grade {expected_grade}")

    def _get_grade_for_marks(self, marks, grade_config):
        """Helper method to get grade for given marks."""
        for line in grade_config.result_line:
            if line.marks_range_from <= marks <= line.marks_range_to:
                return line.grade
        return 'F'  # Default grade if no range matches

    def test_result_template_creation(self):
        """Test result template creation."""
        template = self.env['op.result.template'].create({
            'name': 'Test Result Template',
            'grade_configuration_id': self.grade_config.id,
        })
        
        self.assertEqual(template.name, 'Test Result Template',
                        "Template name should be set")
        self.assertEqual(template.grade_configuration_id, self.grade_config,
                        "Grade configuration should be linked")

    def test_result_template_grade_configuration_relation(self):
        """Test relationship between result template and grade configuration."""
        template = self.env['op.result.template'].create({
            'name': 'Relation Test Template',
            'grade_configuration_id': self.grade_config.id,
        })
        
        # Test that template can access grade lines through configuration
        grade_lines = template.grade_configuration_id.result_line
        self.assertGreater(len(grade_lines), 0, "Should have grade lines")

    def test_multiple_grade_configurations(self):
        """Test multiple grade configurations with different scales."""
        # Create 10-point grading system
        ten_point_config = self.env['op.grade.configuration'].create({
            'name': '10-Point Grading',
            'result_line': [
                (0, 0, {'name': '10', 'marks_range_from': 90, 'marks_range_to': 100, 'grade': '10'}),
                (0, 0, {'name': '9', 'marks_range_from': 80, 'marks_range_to': 89, 'grade': '9'}),
                (0, 0, {'name': '8', 'marks_range_from': 70, 'marks_range_to': 79, 'grade': '8'}),
                (0, 0, {'name': '7', 'marks_range_from': 60, 'marks_range_to': 69, 'grade': '7'}),
                (0, 0, {'name': '6', 'marks_range_from': 50, 'marks_range_to': 59, 'grade': '6'}),
                (0, 0, {'name': 'Fail', 'marks_range_from': 0, 'marks_range_to': 49, 'grade': 'F'}),
            ],
        })
        
        # Test grade calculation with 10-point system
        self.assertEqual(self._get_grade_for_marks(95, ten_point_config), '10')
        self.assertEqual(self._get_grade_for_marks(85, ten_point_config), '9')
        self.assertEqual(self._get_grade_for_marks(45, ten_point_config), 'F')

    def test_grade_configuration_validation_completeness(self):
        """Test that grade configuration covers all possible marks."""
        # Create incomplete grade configuration (missing 0-59 range)
        incomplete_config = self.env['op.grade.configuration'].create({
            'name': 'Incomplete Grading',
            'result_line': [
                (0, 0, {'name': 'A', 'marks_range_from': 80, 'marks_range_to': 100, 'grade': 'A'}),
                (0, 0, {'name': 'B', 'marks_range_from': 60, 'marks_range_to': 79, 'grade': 'B'}),
                # Missing 0-59 range
            ],
        })
        
        # Test that marks below 60 return default grade
        grade = self._get_grade_for_marks(45, incomplete_config)
        self.assertEqual(grade, 'F', "Should return default grade for uncovered range")

    def test_grade_boundary_conditions(self):
        """Test grade calculation at boundary conditions."""
        boundary_tests = [
            (100, 'A+'),  # Upper boundary
            (90, 'A+'),   # Lower boundary of A+
            (89, 'A'),    # Upper boundary of A (just below A+)
            (80, 'A'),    # Lower boundary of A
            (79, 'B'),    # Just below A
            (0, 'F'),     # Minimum possible marks
        ]
        
        for marks, expected_grade in boundary_tests:
            with self.subTest(marks=marks):
                grade = self._get_grade_for_marks(marks, self.grade_config)
                self.assertEqual(grade, expected_grade,
                               f"Boundary test: {marks} should give {expected_grade}")

    def test_custom_grade_symbols(self):
        """Test grade configuration with custom grade symbols."""
        custom_config = self.env['op.grade.configuration'].create({
            'name': 'Custom Symbol Grading',
            'result_line': [
                (0, 0, {'name': 'Excellent', 'marks_range_from': 90, 'marks_range_to': 100, 'grade': 'E'}),
                (0, 0, {'name': 'Very Good', 'marks_range_from': 80, 'marks_range_to': 89, 'grade': 'VG'}),
                (0, 0, {'name': 'Good', 'marks_range_from': 70, 'marks_range_to': 79, 'grade': 'G'}),
                (0, 0, {'name': 'Satisfactory', 'marks_range_from': 60, 'marks_range_to': 69, 'grade': 'S'}),
                (0, 0, {'name': 'Needs Improvement', 'marks_range_from': 0, 'marks_range_to': 59, 'grade': 'NI'}),
            ],
        })
        
        # Test custom grade calculation
        self.assertEqual(self._get_grade_for_marks(95, custom_config), 'E')
        self.assertEqual(self._get_grade_for_marks(85, custom_config), 'VG')
        self.assertEqual(self._get_grade_for_marks(45, custom_config), 'NI')

    def test_percentage_based_grading(self):
        """Test percentage-based grading system."""
        # Create percentage-based configuration
        percentage_config = self.env['op.grade.configuration'].create({
            'name': 'Percentage Grading',
            'result_line': [
                (0, 0, {'name': '90-100%', 'marks_range_from': 90, 'marks_range_to': 100, 'grade': 'A+'}),
                (0, 0, {'name': '80-89%', 'marks_range_from': 80, 'marks_range_to': 89, 'grade': 'A'}),
                (0, 0, {'name': '70-79%', 'marks_range_from': 70, 'marks_range_to': 79, 'grade': 'B'}),
                (0, 0, {'name': '60-69%', 'marks_range_from': 60, 'marks_range_to': 69, 'grade': 'C'}),
                (0, 0, {'name': '50-59%', 'marks_range_from': 50, 'marks_range_to': 59, 'grade': 'D'}),
                (0, 0, {'name': 'Below 50%', 'marks_range_from': 0, 'marks_range_to': 49, 'grade': 'F'}),
            ],
        })
        
        # Test percentage calculations
        test_marks = [95, 85, 75, 65, 55, 45]
        expected_grades = ['A+', 'A', 'B', 'C', 'D', 'F']
        
        for marks, expected in zip(test_marks, expected_grades):
            grade = self._get_grade_for_marks(marks, percentage_config)
            self.assertEqual(grade, expected, f"{marks}% should give grade {expected}")

    def test_grade_configuration_copy(self):
        """Test copying grade configuration."""
        original_config = self.grade_config
        
        # Copy configuration
        copied_config = original_config.copy({'name': 'Copied Grading System'})
        
        self.assertEqual(copied_config.name, 'Copied Grading System',
                        "Copied config should have new name")
        self.assertEqual(len(copied_config.result_line), len(original_config.result_line),
                        "Copied config should have same number of grade lines")

    def test_result_template_with_multiple_subjects(self):
        """Test result template usage across multiple subjects."""
        # Create result template
        template = self.env['op.result.template'].create({
            'name': 'Multi-Subject Template',
            'grade_configuration_id': self.grade_config.id,
        })
        
        # Test template can be used for different subjects
        subjects = [self.subject1, self.subject2]
        
        for subject in subjects:
            # Simulate using template for subject grading
            grade_config = template.grade_configuration_id
            test_grade = self._get_grade_for_marks(85, grade_config)
            self.assertEqual(test_grade, 'A', f"Template should work for {subject.name}")

    def test_grade_statistics_calculation(self):
        """Test calculation of grade distribution statistics."""
        # Sample marks data
        marks_data = [95, 88, 82, 76, 68, 61, 55, 45, 38, 25]
        
        # Calculate grade distribution
        grade_distribution = {}
        for marks in marks_data:
            grade = self._get_grade_for_marks(marks, self.grade_config)
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Verify distribution
        expected_distribution = {
            'A+': 1,  # 95
            'A': 2,   # 88, 82
            'B': 1,   # 76
            'C': 2,   # 68, 61
            'F': 4,   # 55, 45, 38, 25
        }
        
        self.assertEqual(grade_distribution, expected_distribution,
                        "Grade distribution should match expected values")

    def test_grade_configuration_export_import(self):
        """Test export/import functionality for grade configurations."""
        # Prepare export data
        export_data = {
            'name': self.grade_config.name,
            'result_lines': []
        }
        
        for line in self.grade_config.result_line:
            export_data['result_lines'].append({
                'name': line.name,
                'marks_range_from': line.marks_range_from,
                'marks_range_to': line.marks_range_to,
                'grade': line.grade,
            })
        
        # Verify export data structure
        self.assertEqual(export_data['name'], 'Standard Grading')
        self.assertEqual(len(export_data['result_lines']), 5)
        
        # Test import (create new config from exported data)
        imported_config = self.env['op.grade.configuration'].create({
            'name': f"Imported - {export_data['name']}",
            'result_line': [
                (0, 0, {
                    'name': line['name'],
                    'marks_range_from': line['marks_range_from'],
                    'marks_range_to': line['marks_range_to'],
                    'grade': line['grade'],
                })
                for line in export_data['result_lines']
            ],
        })
        
        # Verify imported configuration works correctly
        test_grade = self._get_grade_for_marks(85, imported_config)
        self.assertEqual(test_grade, 'A', "Imported config should work correctly")

    def test_grade_configuration_performance(self):
        """Test performance of grade calculation with large datasets."""
        # Generate large marks dataset
        large_marks_data = list(range(0, 101, 1))  # 0 to 100, step 1
        
        start_time = self.env.now()
        
        # Calculate grades for all marks
        calculated_grades = []
        for marks in large_marks_data:
            grade = self._get_grade_for_marks(marks, self.grade_config)
            calculated_grades.append(grade)
        
        end_time = self.env.now()
        calculation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(calculated_grades), 101, "Should calculate 101 grades")
        self.assertLess(calculation_time, 1.0, 
                       "Grade calculation should complete within 1 second")
        
        # Verify correctness of some calculations
        self.assertEqual(calculated_grades[95], 'A+', "95 should give A+")
        self.assertEqual(calculated_grades[85], 'A', "85 should give A")
        self.assertEqual(calculated_grades[45], 'F', "45 should give F")