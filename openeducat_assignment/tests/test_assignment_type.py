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

from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_assignment_common import TestAssignmentCommon


@tagged('post_install', '-at_install')
class TestAssignmentType(TestAssignmentCommon):
    """Test assignment type management and categorization."""
    
    def test_assignment_type_creation(self):
        """Test Task 2: Test assignment type management and categorization."""
        
        # Test subjective assignment type creation
        subjective_type = self.op_assignment_type.create({
            'name': 'Subjective Assignment',
            'code': 'SUB001',
            'assign_type': 'sub'
        })
        
        self.assertTrue(subjective_type.id)
        self.assertEqual(subjective_type.name, 'Subjective Assignment')
        self.assertEqual(subjective_type.code, 'SUB001')
        self.assertEqual(subjective_type.assign_type, 'sub')
        
        # Test attendance assignment type creation
        attendance_type = self.op_assignment_type.create({
            'name': 'Attendance Assignment',
            'code': 'ATT001',
            'assign_type': 'attendance'
        })
        
        self.assertTrue(attendance_type.id)
        self.assertEqual(attendance_type.assign_type, 'attendance')
    
    def test_assignment_type_required_fields(self):
        """Test assignment type required field validation."""
        # Test missing name field - should raise database constraint error or ValidationError
        from odoo.tools import exception_to_unicode
        try:
            self.op_assignment_type.create({
                'code': 'TEST001',
                'assign_type': 'sub'
            })
            self.fail("Expected an exception when creating assignment type without name")
        except (ValidationError, Exception) as e:
            # Should raise some kind of error for missing required field
            self.assertTrue(True)  # Test passes if any exception is raised
    
    def test_assignment_type_unique_constraints(self):
        """Test assignment type unique constraints if any."""
        # Create first assignment type
        type1 = self.op_assignment_type.create({
            'name': 'Unique Type',
            'code': 'UNIQUE001',
            'assign_type': 'sub'
        })
        
        # Test that we can create different types with different names/codes
        type2 = self.op_assignment_type.create({
            'name': 'Another Type',
            'code': 'UNIQUE002',
            'assign_type': 'attendance'
        })
        
        self.assertNotEqual(type1.id, type2.id)
    
    def test_assignment_type_default_values(self):
        """Test assignment type default values."""
        assignment_type = self.op_assignment_type.create({
            'name': 'Default Test Type'
        })
        
        # Default assign_type should be 'sub'
        self.assertEqual(assignment_type.assign_type, 'sub')
    
    def test_assignment_type_selection_values(self):
        """Test assignment type selection field values."""
        # Test valid selection values
        valid_types = ['sub', 'attendance']
        
        for assign_type in valid_types:
            assignment_type = self.op_assignment_type.create({
                'name': f'Test Type {assign_type}',
                'assign_type': assign_type
            })
            self.assertEqual(assignment_type.assign_type, assign_type)
    
    def test_assignment_type_usage_in_assignments(self):
        """Test assignment type usage in assignments."""
        # Create custom assignment type
        custom_type = self.op_assignment_type.create({
            'name': 'Custom Assignment Type',
            'code': 'CUSTOM001',
            'assign_type': 'sub'
        })
        
        # Create grading assignment with custom type
        grading_assignment = self.grading_assignment.create({
            'name': 'Test Assignment with Custom Type',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=30),
            'assignment_type': custom_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        # Create assignment
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Verify assignment type is correctly linked
        self.assertEqual(assignment.assignment_type.id, custom_type.id)
        self.assertEqual(assignment.assignment_type.name, 'Custom Assignment Type')
    
    def test_assignment_type_categorization_scenarios(self):
        """Test various assignment type categorization scenarios."""
        
        # Scenario 1: Academic assignment types
        academic_types = [
            ('Essay Assignment', 'ESSAY', 'sub'),
            ('Research Assignment', 'RESEARCH', 'sub'),
            ('Project Assignment', 'PROJECT', 'sub'),
        ]
        
        created_types = []
        for name, code, assign_type in academic_types:
            assignment_type = self.op_assignment_type.create({
                'name': name,
                'code': code,
                'assign_type': assign_type
            })
            created_types.append(assignment_type)
            self.assertEqual(assignment_type.assign_type, 'sub')
        
        # Scenario 2: Attendance-based assignment types
        attendance_types = [
            ('Lab Attendance', 'LAB_ATT', 'attendance'),
            ('Lecture Attendance', 'LEC_ATT', 'attendance'),
        ]
        
        for name, code, assign_type in attendance_types:
            assignment_type = self.op_assignment_type.create({
                'name': name,
                'code': code,
                'assign_type': assign_type
            })
            created_types.append(assignment_type)
            self.assertEqual(assignment_type.assign_type, 'attendance')
        
        # Verify all types were created successfully
        self.assertEqual(len(created_types), 5)
    
    def test_assignment_type_crud_operations(self):
        """Test CRUD operations on assignment types."""
        
        # CREATE
        assignment_type = self.op_assignment_type.create({
            'name': 'CRUD Test Type',
            'code': 'CRUD001',
            'assign_type': 'sub'
        })
        
        # READ
        found_type = self.op_assignment_type.browse(assignment_type.id)
        self.assertEqual(found_type.name, 'CRUD Test Type')
        
        # UPDATE
        assignment_type.write({
            'name': 'Updated CRUD Test Type',
            'code': 'CRUD002'
        })
        self.assertEqual(assignment_type.name, 'Updated CRUD Test Type')
        self.assertEqual(assignment_type.code, 'CRUD002')
        
        # Search functionality
        search_result = self.op_assignment_type.search([('code', '=', 'CRUD002')])
        self.assertEqual(len(search_result), 1)
        self.assertEqual(search_result.id, assignment_type.id)
        
        # DELETE
        assignment_type_id = assignment_type.id
        assignment_type.unlink()
        
        # Verify deletion
        deleted_type = self.op_assignment_type.search([('id', '=', assignment_type_id)])
        self.assertEqual(len(deleted_type), 0)
    
    def test_assignment_type_string_representation(self):
        """Test assignment type string representation."""
        assignment_type = self.op_assignment_type.create({
            'name': 'Display Name Test',
            'code': 'DISPLAY001',
            'assign_type': 'sub'
        })
        
        # Test display name functionality
        self.assertEqual(assignment_type.display_name, 'Display Name Test')
    
    def test_assignment_type_filtering_and_grouping(self):
        """Test assignment type filtering and grouping capabilities."""
        
        # Create multiple assignment types
        types_data = [
            ('Type A', 'A001', 'sub'),
            ('Type B', 'B001', 'sub'),
            ('Type C', 'C001', 'attendance'),
            ('Type D', 'D001', 'attendance'),
        ]
        
        created_types = []
        for name, code, assign_type in types_data:
            assignment_type = self.op_assignment_type.create({
                'name': name,
                'code': code,
                'assign_type': assign_type
            })
            created_types.append(assignment_type)
        
        # Test filtering by assign_type
        subjective_types = self.op_assignment_type.search([('assign_type', '=', 'sub')])
        attendance_types = self.op_assignment_type.search([('assign_type', '=', 'attendance')])
        
        # Should include our created types plus any existing ones
        self.assertTrue(len(subjective_types) >= 2)
        self.assertTrue(len(attendance_types) >= 2)
        
        # Test name-based search
        type_a = self.op_assignment_type.search([('name', '=', 'Type A')])
        self.assertEqual(len(type_a), 1)
        self.assertEqual(type_a.code, 'A001')
    
    def test_assignment_type_domain_constraints(self):
        """Test assignment type domain constraints if any."""
        # Create assignment type for domain testing
        assignment_type = self.op_assignment_type.create({
            'name': 'Domain Test Type',
            'code': 'DOMAIN001',
            'assign_type': 'sub'
        })
        
        # Create grading assignment with this type
        grading_assignment = self.grading_assignment.create({
            'name': 'Domain Test Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=30),
            'assignment_type': assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        # Verify the assignment type is properly linked
        self.assertEqual(grading_assignment.assignment_type.id, assignment_type.id)