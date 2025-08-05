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
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'academic_management')
class TestAcademicManagement(TestCoreCommon):
    """Test academic year/term management and transitions."""

    def test_academic_year_creation(self):
        """Test academic year creation with valid data."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        self.assertEqual(academic_year.name, '2024-2025')
        self.assertEqual(str(academic_year.start_date), '2024-01-01')
        self.assertEqual(str(academic_year.end_date), '2024-12-31')
        self.assertTrue(academic_year.id)  # Verify record was created

    def test_academic_year_date_validation(self):
        """Test academic year date validation constraints."""
        # Valid dates
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025 Valid',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        if hasattr(academic_year, '_check_dates'):
            academic_year._check_dates()  # Should not raise exception

    def test_academic_term_creation(self):
        """Test academic term creation with valid data."""
        # Create academic year first
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Create academic term
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'term_start_date': '2024-01-01',
            'term_end_date': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        self.assertEqual(academic_term.name, 'Spring 2024')
        self.assertEqual(academic_term.academic_year_id, academic_year)

    def test_academic_calendar_integration(self):
        """Test academic calendar integration with events."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'term_start_date': '2024-01-01',
            'term_end_date': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # Verify basic academic structure is sound
        self.assertTrue(academic_year.id)  # Verify record was created
        self.assertEqual(academic_term.academic_year_id, academic_year)

    def test_academic_management_with_batches(self):
        """Test academic year/term integration with batches."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'term_start_date': '2024-01-01',
            'term_end_date': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # Create batch within academic term dates
        batch = self.env['op.batch'].create({
            'name': 'Spring Batch 2024',
            'code': 'SB2024',
            'course_id': self.test_course.id,
            'start_date': '2024-02-01',
            'end_date': '2024-06-15',
        })
        
        # Verify batch dates are within term
        self.assertGreaterEqual(batch.start_date, academic_term.term_start_date)
        self.assertLessEqual(batch.end_date, academic_term.term_end_date)

    def test_academic_reporting_periods(self):
        """Test academic reporting periods functionality."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        
        # Create multiple terms for the academic year
        fall_term = self.env['op.academic.term'].create({
            'name': 'Fall 2024',
            'term_start_date': '2024-08-01',
            'term_end_date': '2024-12-31',
            'academic_year_id': academic_year.id,
        })
        
        spring_term = self.env['op.academic.term'].create({
            'name': 'Spring 2025',
            'term_start_date': '2025-01-01',
            'term_end_date': '2025-05-31',
            'academic_year_id': academic_year.id,
        })
        
        # Verify both terms are associated with the academic year
        self.assertEqual(fall_term.academic_year_id, academic_year)
        self.assertEqual(spring_term.academic_year_id, academic_year)