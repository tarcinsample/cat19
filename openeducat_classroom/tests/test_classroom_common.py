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


@tagged('post_install', '-at_install', 'openeducat_classroom')
class TestClassroomCommon(TransactionCase):
    """Common test setup for classroom module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for classroom tests."""
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
        cls.op_classroom = cls.env['op.classroom']
        cls.op_asset = cls.env['op.asset']

    def create_classroom(self, **kwargs):
        """Helper method to create classroom."""
        # Generate unique code to avoid constraint violations
        unique_code = kwargs.pop('code', 'TC-' + str(uuid.uuid4())[:8])
        
        vals = {
            'name': kwargs.pop('name', 'Test Classroom'),
            'code': unique_code,
            'capacity': kwargs.pop('capacity', 50),
        }
        
        # Remove invalid fields that don't exist on op.classroom
        invalid_fields = ['type', 'location', 'building', 'floor', 'accessibility_features',
                         'security_level', 'technology_integration', 'max_capacity', 
                         'is_active', 'status', 'room_number']
        for field in invalid_fields:
            kwargs.pop(field, None)
            
        vals.update(kwargs)
        return self.env['op.classroom'].create(vals)

    def create_asset(self, classroom=None, **kwargs):
        """Helper method to create asset."""
        if not classroom:
            classroom = self.create_classroom()
            
        # Create a product for the asset
        product = kwargs.pop('product_id', None)
        if not product:
            product = self.env['product.product'].create({
                'name': kwargs.pop('product_name', 'Test Product'),
                'detailed_type': 'consu',  # Use detailed_type instead of type for Odoo 15+
                'list_price': kwargs.pop('value', 100.0),
            })
            
        vals = {
            'asset_id': classroom.id,  # asset_id is actually the classroom reference
            'product_id': product.id,
            'code': kwargs.pop('code', 'ASSET-' + str(uuid.uuid4())[:8]),
            'product_uom_qty': kwargs.pop('quantity', 1.0),
        }
        
        # Remove invalid fields
        invalid_fields = ['name', 'type', 'classroom_id', 'purchase_date', 'depreciation_rate',
                         'maintenance_schedule', 'status', 'value', 'asset_type']
        for field in invalid_fields:
            kwargs.pop(field, None)
            
        vals.update(kwargs)
        return self.env['op.asset'].create(vals)

    def create_facility_line(self, classroom=None, **kwargs):
        """Helper method to create facility line."""
        # Create facility first if not provided
        facility = kwargs.pop('facility_id', None)
        if not facility:
            facility = self.env['op.facility'].create({
                'name': kwargs.pop('facility_name', 'Test Facility'),
                'code': 'FAC-' + str(uuid.uuid4())[:8],
                'facility_type': 'equipment',
            })
            
        vals = {
            'facility_id': facility.id,
            'quantity': kwargs.pop('quantity', 1.0),
            'classroom_id': classroom.id if classroom else False,
        }
        
        # Remove invalid fields
        invalid_fields = ['name', 'type', 'status', 'description']
        for field in invalid_fields:
            kwargs.pop(field, None)
            
        vals.update(kwargs)
        return self.env['op.facility.line'].create(vals)
