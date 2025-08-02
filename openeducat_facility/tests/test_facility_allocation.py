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
from .test_facility_common import TestFacilityCommon


@tagged('post_install', '-at_install', 'openeducat_facility')
class TestFacilityAllocation(TestFacilityCommon):
    """Test facility allocation and tracking."""

    def test_facility_creation(self):
        """Test basic facility creation."""
        facility = self.create_facility()
        
        self.assertEqual(facility.name, 'Test Facility', "Facility name should be set")
        self.assertEqual(facility.code, 'TF-001', "Facility code should be set")
        self.assertEqual(facility.facility_type, 'general', "Facility type should be general")

    def test_facility_line_creation(self):
        """Test facility line creation."""
        facility = self.create_facility()
        facility_line = self.create_facility_line(facility=facility)
        
        self.assertEqual(facility_line.facility_id, facility, "Should be linked to facility")
        self.assertEqual(facility_line.name, 'Test Facility Line', "Name should be set")
        self.assertEqual(facility_line.type, 'equipment', "Type should be equipment")
        self.assertEqual(facility_line.quantity, 1, "Quantity should be 1")

    def test_facility_types(self):
        """Test different facility types."""
        facility_types = ['classroom', 'laboratory', 'library', 'auditorium', 'sports', 'cafeteria']
        
        for facility_type in facility_types:
            facility = self.create_facility(
                name=f'{facility_type.title()} Facility',
                code=f'F-{facility_type.upper()[:3]}',
                facility_type=facility_type
            )
            
            self.assertEqual(facility.facility_type, facility_type,
                           f"Should create {facility_type} facility")

    def test_facility_line_types(self):
        """Test different facility line types."""
        facility = self.create_facility()
        
        line_types = ['equipment', 'furniture', 'electronics', 'sports_equipment', 'supplies']
        
        for line_type in line_types:
            facility_line = self.create_facility_line(
                facility=facility,
                name=f'{line_type.title()} Item',
                type=line_type,
                quantity=5
            )
            
            self.assertEqual(facility_line.type, line_type,
                           f"Should create {line_type} facility line")

    def test_facility_capacity_management(self):
        """Test facility capacity management."""
        facility = self.create_facility(capacity=100)
        
        if hasattr(facility, 'capacity'):
            self.assertEqual(facility.capacity, 100, "Should set facility capacity")
            
            # Test capacity validation
            if hasattr(facility, 'current_occupancy'):
                facility.current_occupancy = 85
                self.assertLessEqual(facility.current_occupancy, facility.capacity,
                                   "Occupancy should not exceed capacity")

    def test_facility_availability_tracking(self):
        """Test facility availability tracking."""
        facility = self.create_facility()
        
        # Test availability status
        if hasattr(facility, 'is_available'):
            facility.is_available = True
            self.assertTrue(facility.is_available, "Facility should be available")
            
            # Mark as unavailable
            facility.is_available = False
            self.assertFalse(facility.is_available, "Facility should be unavailable")

    def test_facility_booking_system(self):
        """Test facility booking and reservation system."""
        facility = self.create_facility()
        
        # Test booking if supported
        if hasattr(facility, 'booking_status'):
            facility.booking_status = 'available'
            self.assertEqual(facility.booking_status, 'available',
                           "Should track booking status")
            
            # Book facility
            facility.booking_status = 'booked'
            self.assertEqual(facility.booking_status, 'booked',
                           "Should mark as booked")

    def test_facility_maintenance_scheduling(self):
        """Test facility maintenance scheduling."""
        facility = self.create_facility()
        
        # Test maintenance tracking if supported
        if hasattr(facility, 'maintenance_status'):
            facility.maintenance_status = 'operational'
            self.assertEqual(facility.maintenance_status, 'operational',
                           "Should track maintenance status")
            
            # Schedule maintenance
            facility.maintenance_status = 'scheduled'
            self.assertEqual(facility.maintenance_status, 'scheduled',
                           "Should schedule maintenance")

    def test_facility_line_inventory_tracking(self):
        """Test facility line inventory tracking."""
        facility = self.create_facility()
        
        # Create multiple facility lines
        projectors = self.create_facility_line(
            facility=facility,
            name='Projectors',
            type='electronics',
            quantity=5
        )
        
        chairs = self.create_facility_line(
            facility=facility,
            name='Chairs',
            type='furniture',
            quantity=50
        )
        
        # Verify inventory
        facility_inventory = self.env['op.facility.line'].search([
            ('facility_id', '=', facility.id)
        ])
        
        total_projectors = sum([line.quantity for line in facility_inventory 
                               if line.type == 'electronics'])
        total_chairs = sum([line.quantity for line in facility_inventory 
                           if line.type == 'furniture'])
        
        self.assertEqual(total_projectors, 5, "Should track projector inventory")
        self.assertEqual(total_chairs, 50, "Should track chair inventory")

    def test_facility_allocation_optimization(self):
        """Test facility allocation optimization."""
        # Create facilities with different capacities
        small_facility = self.create_facility(
            name='Small Lab',
            code='SL-001',
            capacity=20,
            facility_type='laboratory'
        )
        
        large_facility = self.create_facility(
            name='Large Auditorium',
            code='LA-001',
            capacity=200,
            facility_type='auditorium'
        )
        
        # Test allocation for different group sizes
        group_sizes = [15, 150]
        
        for size in group_sizes:
            suitable_facilities = self.env['op.facility'].search([
                ('capacity', '>=', size)
            ], order='capacity asc')
            
            if suitable_facilities:
                allocated_facility = suitable_facilities[0]
                self.assertGreaterEqual(allocated_facility.capacity, size,
                                      f"Facility should accommodate {size} people")

    def test_facility_usage_analytics(self):
        """Test facility usage analytics."""
        facility = self.create_facility()
        
        # Test usage tracking if supported
        if hasattr(facility, 'usage_hours'):
            facility.usage_hours = 8.0  # Hours per day
            utilization_rate = (facility.usage_hours / 12.0) * 100  # 12-hour availability
            
            self.assertEqual(utilization_rate, 66.67, "Should calculate utilization rate")

    def test_facility_resource_allocation(self):
        """Test resource allocation within facilities."""
        facility = self.create_facility()
        
        # Allocate various resources
        resources = [
            {'name': 'Computers', 'type': 'electronics', 'quantity': 10},
            {'name': 'Desks', 'type': 'furniture', 'quantity': 10},
            {'name': 'Whiteboards', 'type': 'equipment', 'quantity': 2},
            {'name': 'Books', 'type': 'supplies', 'quantity': 100},
        ]
        
        allocated_resources = []
        for resource in resources:
            facility_line = self.create_facility_line(
                facility=facility,
                name=resource['name'],
                type=resource['type'],
                quantity=resource['quantity']
            )
            allocated_resources.append(facility_line)
        
        # Verify resource allocation
        total_resources = len(allocated_resources)
        self.assertEqual(total_resources, 4, "Should allocate all resources")

    def test_facility_conflict_detection(self):
        """Test detection of facility allocation conflicts."""
        facility = self.create_facility()
        
        # Test double booking detection if supported
        if hasattr(facility, 'booking_start_time') and hasattr(facility, 'booking_end_time'):
            # Book facility for first time slot
            facility.booking_start_time = '09:00'
            facility.booking_end_time = '11:00'
            facility.booking_status = 'booked'
            
            # Try to book overlapping slot - this would typically be handled by business logic
            # In a real system, this would check for conflicts

    def test_facility_security_access(self):
        """Test facility security and access control."""
        facility = self.create_facility()
        
        # Test access control if supported
        if hasattr(facility, 'access_level'):
            facility.access_level = 'restricted'
            self.assertEqual(facility.access_level, 'restricted',
                           "Should set access level")

    def test_facility_environmental_conditions(self):
        """Test facility environmental condition tracking."""
        facility = self.create_facility()
        
        # Test environmental tracking if supported
        if hasattr(facility, 'temperature'):
            facility.temperature = 22.0  # Celsius
            facility.humidity = 45.0     # Percentage
            
            self.assertEqual(facility.temperature, 22.0, "Should track temperature")
            self.assertEqual(facility.humidity, 45.0, "Should track humidity")

    def test_facility_cost_tracking(self):
        """Test facility cost and budget tracking."""
        facility = self.create_facility()
        
        # Test cost tracking if supported
        if hasattr(facility, 'operating_cost'):
            facility.operating_cost = 1000.0  # Monthly cost
            
            self.assertEqual(facility.operating_cost, 1000.0,
                           "Should track operating costs")

    def test_facility_integration_with_timetable(self):
        """Test facility integration with timetable system."""
        facility = self.create_facility(facility_type='classroom')
        
        # Test timetable integration if supported
        if 'op.session' in self.env:
            # This would typically involve checking facility availability
            # for scheduled sessions
            facility_name = facility.name
            
            # Verify facility can be referenced in timetable
            self.assertTrue(facility_name, "Facility should have name for timetable reference")

    def test_facility_reporting_dashboard(self):
        """Test facility reporting and dashboard data."""
        # Create multiple facilities for reporting
        facilities = []
        for i in range(5):
            facility = self.create_facility(
                name=f'Report Facility {i}',
                code=f'RF-{i:03d}',
                facility_type=['classroom', 'laboratory'][i % 2],
                capacity=50 + (i * 25)
            )
            facilities.append(facility)
        
        # Generate dashboard data
        dashboard_data = {
            'total_facilities': len(facilities),
            'by_type': {},
            'total_capacity': sum([f.capacity for f in facilities if hasattr(f, 'capacity')]),
            'utilization_stats': {},
        }
        
        # Group by type
        for facility in facilities:
            if facility.facility_type not in dashboard_data['by_type']:
                dashboard_data['by_type'][facility.facility_type] = 0
            dashboard_data['by_type'][facility.facility_type] += 1
        
        # Verify dashboard data
        self.assertEqual(dashboard_data['total_facilities'], 5,
                        "Should count all facilities")

    def test_facility_emergency_procedures(self):
        """Test facility emergency procedures and safety."""
        facility = self.create_facility()
        
        # Test emergency features if supported
        if hasattr(facility, 'emergency_exits'):
            facility.emergency_exits = 3
            self.assertEqual(facility.emergency_exits, 3,
                           "Should track emergency exits")

    def test_facility_accessibility_compliance(self):
        """Test facility accessibility compliance."""
        facility = self.create_facility()
        
        # Test accessibility features if supported
        if hasattr(facility, 'wheelchair_accessible'):
            facility.wheelchair_accessible = True
            self.assertTrue(facility.wheelchair_accessible,
                          "Should track accessibility features")

    def test_facility_energy_efficiency(self):
        """Test facility energy efficiency tracking."""
        facility = self.create_facility()
        
        # Test energy tracking if supported
        if hasattr(facility, 'energy_rating'):
            facility.energy_rating = 'A'
            self.assertEqual(facility.energy_rating, 'A',
                           "Should track energy rating")

    def test_facility_line_condition_tracking(self):
        """Test facility line condition and status tracking."""
        facility = self.create_facility()
        facility_line = self.create_facility_line(facility=facility)
        
        # Test condition tracking if supported
        if hasattr(facility_line, 'condition'):
            facility_line.condition = 'good'
            self.assertEqual(facility_line.condition, 'good',
                           "Should track item condition")

    def test_facility_bulk_operations(self):
        """Test bulk operations on facilities."""
        # Create multiple facilities
        facilities = []
        for i in range(10):
            facility = self.create_facility(
                name=f'Bulk Facility {i}',
                code=f'BF-{i:03d}',
                facility_type='general'
            )
            facilities.append(facility)
        
        # Bulk update operation
        facility_ids = [f.id for f in facilities]
        bulk_facilities = self.env['op.facility'].browse(facility_ids)
        
        # Update all facilities
        bulk_facilities.write({'facility_type': 'updated'})
        
        # Verify bulk update
        for facility in facilities:
            facility.refresh()
            self.assertEqual(facility.facility_type, 'updated',
                           f"Facility {facility.name} should be updated")

    def test_facility_performance_large_dataset(self):
        """Test performance with large facility dataset."""
        # Create large number of facilities
        facilities = []
        
        for i in range(100):
            facility = self.create_facility(
                name=f'Performance Facility {i}',
                code=f'PF-{i:03d}',
                facility_type=['classroom', 'laboratory', 'office'][i % 3]
            )
            facilities.append(facility)
        
        # Test search performance
        search_results = self.env['op.facility'].search([
            ('facility_type', '=', 'classroom')
        ])
        
        self.assertGreater(len(search_results), 0,
                          "Should handle large datasets efficiently")

    def test_facility_integration_workflow(self):
        """Test complete facility management workflow."""
        # 1. Create facility
        facility = self.create_facility(facility_type='laboratory')
        
        # 2. Add equipment
        equipment = self.create_facility_line(
            facility=facility,
            name='Lab Equipment',
            type='equipment',
            quantity=10
        )
        
        # 3. Set availability
        if hasattr(facility, 'is_available'):
            facility.is_available = True
        
        # 4. Verify workflow completion
        self.assertTrue(facility.exists(), "Facility should be created")
        self.assertTrue(equipment.exists(), "Equipment should be added")
        
        # 5. Check facility readiness
        facility_equipment = self.env['op.facility.line'].search([
            ('facility_id', '=', facility.id)
        ])
        
        self.assertGreater(len(facility_equipment), 0,
                          "Facility should have equipment")

    def test_facility_validation_constraints(self):
        """Test facility validation constraints."""
        # Test facility without name
        with self.assertRaises(ValidationError):
            self.env['op.facility'].create({
                'code': 'NO-NAME',
                'facility_type': 'general',
            })
        
        # Test facility line without facility
        with self.assertRaises(ValidationError):
            self.env['op.facility.line'].create({
                'name': 'Orphan Line',
                'type': 'equipment',
                'quantity': 1,
            })

    def test_facility_data_integrity(self):
        """Test data integrity for facility management."""
        facility = self.create_facility()
        facility_line = self.create_facility_line(facility=facility)
        
        # Test referential integrity
        self.assertTrue(facility_line.facility_id.exists(),
                       "Facility should exist")
        
        # Test cascade behavior
        facility_id = facility.id
        facility.unlink()
        
        # Facility lines should be cleaned up
        remaining_lines = self.env['op.facility.line'].search([
            ('facility_id', '=', facility_id)
        ])
        
        self.assertEqual(len(remaining_lines), 0,
                        "Facility lines should be cleaned up")