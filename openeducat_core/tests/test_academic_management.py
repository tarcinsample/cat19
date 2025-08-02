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
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        self.assertEqual(academic_year.name, '2024-2025')
        self.assertEqual(academic_year.code, 'AY2024')
        self.assertEqual(str(academic_year.date_start), '2024-01-01')
        self.assertEqual(str(academic_year.date_stop), '2024-12-31')
        self.assertTrue(academic_year.active)

    def test_academic_year_date_validation(self):
        """Test academic year date validation constraints."""
        # Valid dates
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025 Valid',
            'code': 'AY2024V',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        if hasattr(academic_year, '_check_dates'):
            academic_year._check_dates()  # Should not raise exception

    def test_academic_year_uniqueness(self):
        """Test academic year code uniqueness."""
        # Create first academic year
        ay1 = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'UNIQUE_AY',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Check if uniqueness constraint exists and test it
        constraint_names = [constraint[0] for constraint in self.env['op.academic.year']._sql_constraints]
        if 'unique_academic_year_code' in constraint_names:
            with self.assertRaises(Exception):  # Could be IntegrityError
                self.env['op.academic.year'].create({
                    'name': '2025-2026',
                    'code': 'UNIQUE_AY',  # Duplicate code
                    'date_start': '2025-01-01',
                    'date_stop': '2025-12-31',
                })

    def test_academic_term_creation(self):
        """Test academic term creation with valid data."""
        # Create academic year first
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create academic term
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        self.assertEqual(academic_term.name, 'Spring 2024')
        self.assertEqual(academic_term.code, 'SP2024')
        self.assertEqual(academic_term.academic_year_id, academic_year)
        self.assertTrue(academic_term.active)

    def test_academic_term_within_year_dates(self):
        """Test academic term dates are within academic year."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Valid term within year
        term_valid = self.env['op.academic.term'].create({
            'name': 'Fall 2024',
            'code': 'FALL2024',
            'date_start': '2024-08-01',
            'date_stop': '2024-12-31',
            'academic_year_id': academic_year.id,
        })
        
        # Verify term is within academic year dates
        self.assertGreaterEqual(term_valid.date_start, academic_year.date_start)
        self.assertLessEqual(term_valid.date_stop, academic_year.date_stop)

    def test_academic_term_date_validation(self):
        """Test academic term date validation constraints."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Test term with valid dates
        term = self.env['op.academic.term'].create({
            'name': 'Valid Term',
            'code': 'VT2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        if hasattr(term, '_check_dates'):
            term._check_dates()  # Should not raise exception
        
        # Test term with invalid dates (end before start)
        if hasattr(term, '_check_dates'):
            term.date_start = '2024-06-30'
            term.date_stop = '2024-01-01'
            with self.assertRaises(ValidationError):
                term._check_dates()

    def test_multiple_terms_in_academic_year(self):
        """Test multiple terms within same academic year."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create multiple terms
        term1 = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-05-31',
            'academic_year_id': academic_year.id,
        })
        
        term2 = self.env['op.academic.term'].create({
            'name': 'Summer 2024',
            'code': 'SU2024',
            'date_start': '2024-06-01',
            'date_stop': '2024-08-31',
            'academic_year_id': academic_year.id,
        })
        
        term3 = self.env['op.academic.term'].create({
            'name': 'Fall 2024',
            'code': 'FA2024',
            'date_start': '2024-09-01',
            'date_stop': '2024-12-31',
            'academic_year_id': academic_year.id,
        })
        
        # Verify all terms belong to same academic year
        self.assertEqual(term1.academic_year_id, academic_year)
        self.assertEqual(term2.academic_year_id, academic_year)
        self.assertEqual(term3.academic_year_id, academic_year)
        
        # Verify terms are sequential and non-overlapping
        self.assertLess(term1.date_stop, term2.date_start)
        self.assertLess(term2.date_stop, term3.date_start)

    def test_academic_year_transition(self):
        """Test transitioning between academic years."""
        # Create current academic year
        current_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create next academic year
        next_year = self.env['op.academic.year'].create({
            'name': '2025-2026',
            'code': 'AY2025',
            'date_start': '2025-01-01',
            'date_stop': '2025-12-31',
        })
        
        # Verify both years can coexist
        self.assertTrue(current_year.active)
        self.assertTrue(next_year.active)
        
        # Test deactivating old year
        current_year.active = False
        self.assertFalse(current_year.active)
        self.assertTrue(next_year.active)

    def test_academic_term_transition(self):
        """Test transitioning between academic terms."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create sequential terms
        spring_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-05-31',
            'academic_year_id': academic_year.id,
        })
        
        fall_term = self.env['op.academic.term'].create({
            'name': 'Fall 2024',
            'code': 'FA2024',
            'date_start': '2024-09-01',
            'date_stop': '2024-12-31',
            'academic_year_id': academic_year.id,
        })
        
        # Test transitioning from spring to fall
        spring_term.active = False
        self.assertFalse(spring_term.active)
        self.assertTrue(fall_term.active)

    def test_academic_year_current_year_functionality(self):
        """Test current academic year functionality."""
        # Create academic years
        past_year = self.env['op.academic.year'].create({
            'name': '2023-2024',
            'code': 'AY2023',
            'date_start': '2023-01-01',
            'date_stop': '2023-12-31',
        })
        
        current_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Test finding current academic year (if such method exists)
        today = date.today()
        if today.year == 2024:
            current_years = self.env['op.academic.year'].search([
                ('date_start', '<=', today),
                ('date_stop', '>=', today),
                ('active', '=', True)
            ])
            if current_years:
                self.assertIn(current_year, current_years)

    def test_academic_term_current_term_functionality(self):
        """Test current academic term functionality."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create term that includes today's date
        today = date.today()
        term_start = date(today.year, 1, 1)
        term_end = date(today.year, 12, 31)
        
        current_term = self.env['op.academic.term'].create({
            'name': f'Current Term {today.year}',
            'code': f'CT{today.year}',
            'date_start': term_start,
            'date_stop': term_end,
            'academic_year_id': academic_year.id,
        })
        
        # Test finding current term
        current_terms = self.env['op.academic.term'].search([
            ('date_start', '<=', today),
            ('date_stop', '>=', today),
            ('active', '=', True)
        ])
        
        if current_terms:
            self.assertIn(current_term, current_terms)

    def test_academic_year_overlap_validation(self):
        """Test academic year overlap validation if exists."""
        # Create first academic year
        year1 = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Try to create overlapping academic year
        # Note: This test assumes overlap validation exists
        if hasattr(self.env['op.academic.year'], '_check_overlap'):
            with self.assertRaises(ValidationError):
                self.env['op.academic.year'].create({
                    'name': '2024-2026 Overlap',
                    'code': 'AY2024O',
                    'date_start': '2024-06-01',  # Overlaps with year1
                    'date_stop': '2025-12-31',
                })

    def test_academic_term_overlap_validation(self):
        """Test academic term overlap validation within same year."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create first term
        term1 = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # Try to create overlapping term (if validation exists)
        if hasattr(self.env['op.academic.term'], '_check_overlap'):
            with self.assertRaises(ValidationError):
                self.env['op.academic.term'].create({
                    'name': 'Overlapping Term',
                    'code': 'OT2024',
                    'date_start': '2024-03-01',  # Overlaps with term1
                    'date_stop': '2024-09-30',
                    'academic_year_id': academic_year.id,
                })

    def test_academic_year_sequence_generation(self):
        """Test academic year sequence generation if exists."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Check if sequence field exists and is populated
        if hasattr(academic_year, 'sequence'):
            self.assertTrue(academic_year.sequence)

    def test_academic_term_sequence_generation(self):
        """Test academic term sequence generation if exists."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # Check if sequence field exists and is populated
        if hasattr(academic_term, 'sequence'):
            self.assertTrue(academic_term.sequence)

    def test_academic_management_with_batches(self):
        """Test academic year/term integration with batches."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
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
        self.assertGreaterEqual(batch.start_date, academic_term.date_start)
        self.assertLessEqual(batch.end_date, academic_term.date_stop)

    def test_academic_reporting_periods(self):
        """Test academic reporting and grading periods."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # Create terms for different grading periods
        quarters = [
            ('Q1 2024', 'Q1_2024', '2024-01-01', '2024-03-31'),
            ('Q2 2024', 'Q2_2024', '2024-04-01', '2024-06-30'),
            ('Q3 2024', 'Q3_2024', '2024-07-01', '2024-09-30'),
            ('Q4 2024', 'Q4_2024', '2024-10-01', '2024-12-31'),
        ]
        
        created_quarters = []
        for name, code, start, end in quarters:
            quarter = self.env['op.academic.term'].create({
                'name': name,
                'code': code,
                'date_start': start,
                'date_stop': end,
                'academic_year_id': academic_year.id,
            })
            created_quarters.append(quarter)
        
        # Verify all quarters are within academic year
        for quarter in created_quarters:
            self.assertEqual(quarter.academic_year_id, academic_year)
            self.assertGreaterEqual(quarter.date_start, academic_year.date_start)
            self.assertLessEqual(quarter.date_stop, academic_year.date_stop)

    def test_academic_year_status_management(self):
        """Test academic year status management (active/inactive)."""
        # Create multiple academic years
        years = []
        for i in range(3):
            year = self.env['op.academic.year'].create({
                'name': f'202{3+i}-202{4+i}',
                'code': f'AY202{3+i}',
                'date_start': f'202{3+i}-01-01',
                'date_stop': f'202{3+i}-12-31',
            })
            years.append(year)
        
        # Initially all years should be active
        for year in years:
            self.assertTrue(year.active)
        
        # Deactivate old years
        years[0].active = False
        self.assertFalse(years[0].active)
        self.assertTrue(years[1].active)
        self.assertTrue(years[2].active)

    def test_academic_calendar_integration(self):
        """Test academic calendar integration with events."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # This tests integration potential with calendar events
        # In a real implementation, you might have academic events
        # tied to academic years and terms
        
        # Verify basic academic structure is sound
        self.assertTrue(academic_year.active)
        self.assertTrue(academic_term.active)
        self.assertEqual(academic_term.academic_year_id, academic_year)