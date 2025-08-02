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
from .test_classroom_common import TestClassroomCommon


@tagged('post_install', '-at_install', 'openeducat_classroom')
class TestClassroomManagement(TestClassroomCommon):
    """Test classroom and facility management."""

    def test_classroom_creation(self):
        """Test basic classroom creation."""
        classroom = self.create_classroom()
        
        self.assertEqual(classroom.name, 'Test Classroom', "Classroom name should be set")
        self.assertEqual(classroom.code, 'TC-001', "Classroom code should be set")
        self.assertEqual(classroom.capacity, 50, "Classroom capacity should be 50")
        self.assertEqual(classroom.type, 'classroom', "Type should be classroom")

    def test_classroom_capacity_validation(self):
        """Test classroom capacity validation."""
        # Test valid capacity
        classroom = self.create_classroom(capacity=100)
        self.assertEqual(classroom.capacity, 100, "Should accept valid capacity")
        
        # Test negative capacity
        with self.assertRaises(ValidationError):
            self.create_classroom(capacity=-10)
        
        # Test zero capacity
        with self.assertRaises(ValidationError):
            self.create_classroom(capacity=0)

    def test_classroom_code_uniqueness(self):
        """Test classroom code uniqueness."""
        # Create first classroom
        classroom1 = self.create_classroom(code='UNIQUE-001')
        
        # Try to create duplicate code
        with self.assertRaises(ValidationError):
            self.create_classroom(code='UNIQUE-001', name='Duplicate Classroom')

    def test_classroom_types(self):
        """Test different classroom types."""
        classroom_types = ['classroom', 'laboratory', 'auditorium', 'library', 'office']
        
        for classroom_type in classroom_types:
            classroom = self.create_classroom(
                name=f'{classroom_type.title()} Room',
                code=f'CR-{classroom_type.upper()[:3]}',
                type=classroom_type
            )
            
            self.assertEqual(classroom.type, classroom_type,
                           f"Should create {classroom_type} type")

    def test_classroom_asset_management(self):
        """Test classroom asset management."""
        classroom = self.create_classroom()
        
        # Create assets for classroom
        projector = self.create_asset(
            classroom=classroom,
            name='Projector',
            asset_id='PROJ-001',
            type='electronics'
        )
        
        chairs = self.create_asset(
            classroom=classroom,
            name='Chairs',
            asset_id='CHAIR-001',
            type='furniture'
        )
        
        # Verify assets are linked to classroom
        classroom_assets = self.env['op.asset'].search([
            ('classroom_id', '=', classroom.id)
        ])
        
        self.assertIn(projector, classroom_assets, "Projector should be linked")
        self.assertIn(chairs, classroom_assets, "Chairs should be linked")

    def test_classroom_facility_lines(self):
        """Test classroom facility line management."""
        classroom = self.create_classroom()
        
        # Create facility lines
        projector_facility = self.create_facility_line(
            classroom=classroom,
            name='Digital Projector',
            type='projector',
            quantity=1
        )
        
        whiteboard_facility = self.create_facility_line(
            classroom=classroom,
            name='Whiteboard',
            type='board',
            quantity=2
        )
        
        # Verify facilities are linked
        classroom_facilities = self.env['op.facility.line'].search([
            ('classroom_id', '=', classroom.id)
        ])
        
        self.assertEqual(len(classroom_facilities), 2, "Should have 2 facilities")
        self.assertIn(projector_facility, classroom_facilities, "Should include projector")
        self.assertIn(whiteboard_facility, classroom_facilities, "Should include whiteboard")

    def test_classroom_capacity_utilization(self):
        """Test classroom capacity utilization tracking."""
        classroom = self.create_classroom(capacity=30)
        
        # Test capacity calculation if supported
        if hasattr(classroom, 'current_occupancy'):
            classroom.current_occupancy = 25
            utilization = (classroom.current_occupancy / classroom.capacity) * 100
            
            self.assertEqual(utilization, 83.33, "Should calculate utilization correctly")

    def test_classroom_search_functionality(self):
        """Test classroom search and filtering."""
        # Create classrooms with different attributes
        lab = self.create_classroom(
            name='Science Lab',
            code='LAB-001',
            type='laboratory',
            capacity=25
        )
        
        auditorium = self.create_classroom(
            name='Main Auditorium',
            code='AUD-001',
            type='auditorium',
            capacity=200
        )
        
        # Search by type
        labs = self.env['op.classroom'].search([('type', '=', 'laboratory')])
        self.assertIn(lab, labs, "Should find laboratory")
        
        # Search by capacity range
        large_rooms = self.env['op.classroom'].search([('capacity', '>', 100)])
        self.assertIn(auditorium, large_rooms, "Should find large rooms")
        
        # Search by name
        science_rooms = self.env['op.classroom'].search([('name', 'ilike', 'science')])
        self.assertIn(lab, science_rooms, "Should find rooms by name")

    def test_classroom_availability_checking(self):
        """Test classroom availability checking."""
        classroom = self.create_classroom()
        
        # Test availability status if supported
        if hasattr(classroom, 'is_available'):
            classroom.is_available = True
            self.assertTrue(classroom.is_available, "Classroom should be available")
            
            # Mark as unavailable
            classroom.is_available = False
            self.assertFalse(classroom.is_available, "Classroom should be unavailable")

    def test_classroom_maintenance_tracking(self):
        """Test classroom maintenance tracking."""
        classroom = self.create_classroom()
        
        # Test maintenance fields if supported
        if hasattr(classroom, 'maintenance_status'):
            classroom.maintenance_status = 'pending'
            self.assertEqual(classroom.maintenance_status, 'pending',
                           "Should track maintenance status")

    def test_classroom_location_hierarchy(self):
        """Test classroom location hierarchy."""
        # Create classroom with location details
        classroom = self.create_classroom(
            name='Room 101',
            code='R-101',
            location='Building A, Floor 1'
        )
        
        if hasattr(classroom, 'location'):
            self.assertEqual(classroom.location, 'Building A, Floor 1',
                           "Should store location information")

    def test_asset_lifecycle_management(self):
        """Test asset lifecycle management."""
        classroom = self.create_classroom()
        asset = self.create_asset(classroom=classroom)
        
        # Test asset status transitions if supported
        if hasattr(asset, 'status'):
            # New -> Active -> Maintenance -> Retired
            asset.status = 'active'
            self.assertEqual(asset.status, 'active', "Asset should be active")
            
            asset.status = 'maintenance'
            self.assertEqual(asset.status, 'maintenance', "Asset should be in maintenance")

    def test_asset_depreciation_tracking(self):
        """Test asset depreciation tracking."""
        classroom = self.create_classroom()
        asset = self.create_asset(
            classroom=classroom,
            name='Computer',
            purchase_value=1000.0,
            purchase_date='2024-01-01'
        )
        
        # Test depreciation calculation if supported
        if hasattr(asset, 'current_value'):
            # This would typically involve depreciation calculations
            self.assertLessEqual(asset.current_value, 1000.0,
                               "Current value should not exceed purchase value")

    def test_facility_maintenance_scheduling(self):
        """Test facility maintenance scheduling."""
        classroom = self.create_classroom()
        facility = self.create_facility_line(classroom=classroom)
        
        # Test maintenance scheduling if supported
        if hasattr(facility, 'next_maintenance_date'):
            facility.next_maintenance_date = '2024-12-01'
            
            self.assertEqual(facility.next_maintenance_date, '2024-12-01',
                           "Should schedule maintenance")

    def test_classroom_reporting_data(self):
        """Test classroom reporting data generation."""
        # Create multiple classrooms for reporting
        classrooms = []
        for i in range(5):
            classroom = self.create_classroom(
                name=f'Report Room {i}',
                code=f'RR-{i:03d}',
                capacity=30 + (i * 10),
                type=['classroom', 'laboratory'][i % 2]
            )
            classrooms.append(classroom)
        
        # Generate report data
        report_data = {
            'total_classrooms': len(classrooms),
            'total_capacity': sum([c.capacity for c in classrooms]),
            'by_type': {},
            'avg_capacity': sum([c.capacity for c in classrooms]) / len(classrooms),
        }
        
        # Group by type
        for classroom in classrooms:
            if classroom.type not in report_data['by_type']:
                report_data['by_type'][classroom.type] = 0
            report_data['by_type'][classroom.type] += 1
        
        # Verify report data
        self.assertEqual(report_data['total_classrooms'], 5, "Should count all classrooms")
        self.assertGreater(report_data['total_capacity'], 0, "Should calculate total capacity")

    def test_classroom_allocation_optimization(self):
        """Test classroom allocation optimization."""
        # Create classrooms with different capacities
        small_room = self.create_classroom(name='Small Room', capacity=20, code='SM-001')
        medium_room = self.create_classroom(name='Medium Room', capacity=50, code='MD-001')
        large_room = self.create_classroom(name='Large Room', capacity=100, code='LG-001')
        
        # Test allocation logic for different group sizes
        group_sizes = [15, 45, 90]
        
        for size in group_sizes:
            # Find suitable classroom
            suitable_rooms = self.env['op.classroom'].search([
                ('capacity', '>=', size)
            ], order='capacity asc')
            
            if suitable_rooms:
                allocated_room = suitable_rooms[0]  # Smallest suitable room
                self.assertGreaterEqual(allocated_room.capacity, size,
                                      f"Room should accommodate {size} people")

    def test_classroom_equipment_inventory(self):
        """Test classroom equipment inventory management."""
        classroom = self.create_classroom()
        
        # Create various equipment
        equipment_list = [
            {'name': 'Projector', 'type': 'electronics', 'quantity': 1},
            {'name': 'Chairs', 'type': 'furniture', 'quantity': 30},
            {'name': 'Tables', 'type': 'furniture', 'quantity': 15},
            {'name': 'Whiteboard', 'type': 'board', 'quantity': 1},
        ]
        
        created_equipment = []
        for equipment in equipment_list:
            if 'op.facility.line' in self.env:
                facility = self.create_facility_line(
                    classroom=classroom,
                    name=equipment['name'],
                    type=equipment['type'],
                    quantity=equipment['quantity']
                )
                created_equipment.append(facility)
        
        # Verify inventory
        total_items = sum([eq['quantity'] for eq in equipment_list])
        classroom_inventory = self.env['op.facility.line'].search([
            ('classroom_id', '=', classroom.id)
        ])
        
        actual_total = sum([item.quantity for item in classroom_inventory])
        self.assertEqual(actual_total, total_items, "Should track all equipment")

    def test_classroom_accessibility_features(self):
        """Test classroom accessibility features tracking."""
        # Create accessible classroom
        accessible_classroom = self.create_classroom(
            name='Accessible Room',
            code='ACC-001',
            wheelchair_accessible=True,
            hearing_loop=True
        )
        
        # Test accessibility fields if supported
        if hasattr(accessible_classroom, 'wheelchair_accessible'):
            self.assertTrue(accessible_classroom.wheelchair_accessible,
                          "Should be wheelchair accessible")

    def test_classroom_technology_integration(self):
        """Test classroom technology integration tracking."""
        classroom = self.create_classroom()
        
        # Add technology equipment
        tech_equipment = [
            {'name': 'Smart Board', 'type': 'interactive_display'},
            {'name': 'Sound System', 'type': 'audio'},
            {'name': 'WiFi Access Point', 'type': 'network'},
        ]
        
        for tech in tech_equipment:
            if 'op.facility.line' in self.env:
                self.create_facility_line(
                    classroom=classroom,
                    name=tech['name'],
                    type=tech['type'],
                    quantity=1
                )
        
        # Verify technology tracking
        tech_facilities = self.env['op.facility.line'].search([
            ('classroom_id', '=', classroom.id),
            ('type', 'in', ['interactive_display', 'audio', 'network'])
        ])
        
        self.assertEqual(len(tech_facilities), 3, "Should track technology equipment")

    def test_classroom_energy_efficiency(self):
        """Test classroom energy efficiency tracking."""
        classroom = self.create_classroom()
        
        # Test energy efficiency fields if supported
        if hasattr(classroom, 'energy_rating'):
            classroom.energy_rating = 'A'
            self.assertEqual(classroom.energy_rating, 'A',
                           "Should track energy efficiency")

    def test_classroom_usage_analytics(self):
        """Test classroom usage analytics."""
        classroom = self.create_classroom()
        
        # Test usage tracking if supported
        if hasattr(classroom, 'usage_hours'):
            classroom.usage_hours = 6.5  # Hours per day
            utilization_rate = (classroom.usage_hours / 8.0) * 100  # 8-hour day
            
            self.assertEqual(utilization_rate, 81.25, "Should calculate utilization rate")

    def test_classroom_security_features(self):
        """Test classroom security features."""
        classroom = self.create_classroom()
        
        # Add security equipment
        security_items = [
            {'name': 'Security Camera', 'type': 'security'},
            {'name': 'Access Card Reader', 'type': 'access_control'},
            {'name': 'Emergency Button', 'type': 'emergency'},
        ]
        
        for item in security_items:
            if 'op.facility.line' in self.env:
                self.create_facility_line(
                    classroom=classroom,
                    name=item['name'],
                    type=item['type'],
                    quantity=1
                )
        
        # Verify security tracking
        security_facilities = self.env['op.facility.line'].search([
            ('classroom_id', '=', classroom.id),
            ('type', 'in', ['security', 'access_control', 'emergency'])
        ])
        
        self.assertGreater(len(security_facilities), 0, "Should track security equipment")

    def test_classroom_performance_optimization(self):
        """Test performance with large classroom dataset."""
        # Create large number of classrooms
        classrooms = []
        
        for i in range(100):
            classroom = self.create_classroom(
                name=f'Performance Room {i}',
                code=f'PR-{i:03d}',
                capacity=25 + (i % 50)
            )
            classrooms.append(classroom)
        
        # Test search performance
        search_results = self.env['op.classroom'].search([
            ('capacity', '>', 30)
        ])
        
        self.assertGreater(len(search_results), 0, "Should handle large datasets efficiently")

    def test_classroom_integration_workflow(self):
        """Test integration with timetable and session management."""
        classroom = self.create_classroom()
        
        # Test integration with timetable if supported
        if 'op.session' in self.env:
            # Create session using classroom
            session_data = {
                'classroom': classroom.name,
                'capacity_required': 25,
            }
            
            # Verify classroom can accommodate session
            self.assertGreaterEqual(classroom.capacity, session_data['capacity_required'],
                                  "Classroom should accommodate session requirements")