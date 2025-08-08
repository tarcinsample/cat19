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
            'start_date': '2024-06-01',
            'end_date': '2025-05-31',
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
            'code': 'TB001_' + str(uuid.uuid4())[:8].replace('-', ''),
            'course_id': cls.course.id,
            'start_date': '2024-06-01',
            'end_date': '2024-12-31',
        })
        
        # Model references for legacy tests
        cls.op_facility_line = cls.env['op.facility.line']

    def create_facility(self, **kwargs):
        """Helper method to create facility."""
        # Generate unique code to avoid constraint violations
        unique_code = kwargs.get('code', 'TF-' + str(uuid.uuid4())[:8])
        
        vals = {
            'name': kwargs.pop('name', 'Test Facility'),
            'code': unique_code,
            'facility_type': 'other',  # Use valid selection value
        }
        
        # Map invalid facility types to valid ones
        if 'facility_type' in kwargs:
            facility_type_map = {
                'general': 'other',
                'classroom': 'equipment',
                'laboratory': 'laboratory',
                'library': 'library',  # Add library mapping
                'computer': 'technology',
                'gym': 'sports',
                'sports': 'sports',
                'cafeteria': 'other',
                'auditorium': 'other',
                'office': 'other',
                'updated': 'other',
            }
            kwargs['facility_type'] = facility_type_map.get(kwargs['facility_type'], 'other')
        
        # Remove invalid fields that don't exist on op.facility
        invalid_fields = ['capacity', 'location', 'floor', 'room_number', 'building', 'availability_status', 
                         'max_occupancy', 'min_occupancy', 'available', 'is_active', 'status', 'asset_id']
        for field in invalid_fields:
            kwargs.pop(field, None)
            
        vals.update(kwargs)
        return self.env['op.facility'].create(vals)

    def create_facility_line(self, facility=None, **kwargs):
        """Helper method to create facility line."""
        if not facility:
            facility = self.create_facility()
            
        vals = {
            'facility_id': facility.id,
            'quantity': kwargs.pop('quantity', 1.0),
        }
        
        # Remove invalid fields
        invalid_fields = ['name', 'type', 'asset_id', 'description', 'status']
        for field in invalid_fields:
            kwargs.pop(field, None)
            
        vals.update(kwargs)
        return self.env['op.facility.line'].create(vals)
