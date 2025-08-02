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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_facility')
class TestFacilityCommon(TransactionCase):
    """Common test setup for facility module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for facility tests."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create academic year
        cls.academic_year = cls.env['op.academic.year'].create({
            'name': 'Test Year 2024-25',
            'code': 'TY24',
            'date_start': '2024-06-01',
            'date_stop': '2025-05-31',
        })
        
        # Create department
        cls.department = cls.env['op.department'].create({
            'name': 'Test Department',
            'code': 'TD001',
        })
        
        # Create course
        cls.course = cls.env['op.course'].create({
            'name': 'Test Course',
            'code': 'TC001',
            'department_id': cls.department.id,
        })
        
        # Create batch
        cls.batch = cls.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'TB001',
            'course_id': cls.course.id,
            'start_date': '2024-06-01',
            'end_date': '2024-12-31',
        })

    def create_facility(self, **kwargs):
        """Helper method to create facility."""
        vals = {
            'name': 'Test Facility',
            'code': 'TF-001',
            'facility_type': 'general',
        }
        vals.update(kwargs)
        return self.env['op.facility'].create(vals)

    def create_facility_line(self, facility=None, **kwargs):
        """Helper method to create facility line."""
        vals = {
            'name': 'Test Facility Line',
            'type': 'equipment',
            'quantity': 1,
        }
        if facility:
            vals['facility_id'] = facility.id
        vals.update(kwargs)
        return self.env['op.facility.line'].create(vals)
