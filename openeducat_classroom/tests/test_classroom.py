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

from logging import info

from .test_classroom_common import TestClassroomCommon


class TestClassroom(TestClassroomCommon):

    def setUp(self):
        super(TestClassroom, self).setUp()

    def test_case_classroom_1(self):
        # Create test classroom instead of searching
        classroom = self.create_classroom(
            course_id=self.course.id,
            batch_id=self.batch.id
        )
        
        # Create facilities and assets for the classroom
        facility_line = self.create_facility_line(classroom=classroom)
        asset = self.create_asset(classroom=classroom)
        
        self.assertTrue(classroom.exists(), 'Classroom should be created')
        info('      Class Name: %s' % classroom.name)
        info('      Code : %s' % classroom.code)
        if classroom.course_id:
            info('      Course Name : %s' % classroom.course_id.name)
        info('      Capacity : %s' % classroom.capacity)
        
        # Test onchange if it exists
        if hasattr(classroom, 'onchange_course'):
            classroom.onchange_course()


class TestAsset(TestClassroomCommon):

    def setUp(self):
        super(TestAsset, self).setUp()

    def test_case_1_asset(self):
        product = self.env['product.product'].create({
            'default_code': 'FIFO',
            'name': 'Chairs',
            'categ_id': self.env.ref('product.product_category_1').id,
            'list_price': 100.0,
            'standard_price': 70.0,
            'uom_id': self.env.ref('uom.product_uom_kgm').id,
            'uom_po_id': self.env.ref('uom.product_uom_kgm').id,
            'description': 'FIFO Ice Cream',
        })
        # Create classroom first instead of using XML ID
        classroom = self.create_classroom()
        
        assets = self.op_asset.create({
            'asset_id': classroom.id,  # Use created classroom
            'product_id': product.id,
            'code': 'ASSET-001',  # Code should be string
            'product_uom_qty': 11
        })
        for record in assets:
            info('      Asset Name: %s' % record.asset_id.name)
            info('      Product Name : %s' % record.product_id.name)
            info('      Product Quantity : %s' % record.product_uom_qty)
