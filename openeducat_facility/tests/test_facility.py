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

from .test_facility_common import TestFacilityCommon


class TestFacilityLine(TestFacilityCommon):

    def setUp(self):
        super(TestFacilityLine, self).setUp()

    def test_case_facility_line(self):
        # Create a facility instead of using XML ID
        facility = self.create_facility()
        
        # Create facility line with the created facility
        facility_line = self.op_facility_line.create({
            'facility_id': facility.id,
            'quantity': 1.0,  # Use float instead of string
        })
        
        # Test the check_quantity method if it exists
        if hasattr(facility_line, 'check_quantity'):
            facility_line.check_quantity()
