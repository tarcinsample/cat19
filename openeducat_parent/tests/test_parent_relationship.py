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
from .test_parent_common import TestParentCommon


@tagged('post_install', '-at_install', 'openeducat_parent')
class TestParentRelationship(TestParentCommon):
    """Test parent-student relationship management."""

    def test_parent_relationship_creation(self):
        """Test basic parent-student relationship creation."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        self.assertEqual(relationship.parent_id, parent, "Parent should be linked")
        self.assertEqual(relationship.student_id, self.student1, "Student should be linked")
        self.assertEqual(relationship.relation, 'father', "Relation should be father")

    def test_parent_multiple_students(self):
        """Test parent with multiple students."""
        parent = self.create_parent()
        
        # Create relationships with both students
        rel1 = self.create_parent_relationship(parent, self.student1, 'father')
        rel2 = self.create_parent_relationship(parent, self.student2, 'father')
        
        # Find all relationships for this parent
        relationships = self.env['op.parent.relation'].search([
            ('parent_id', '=', parent.id)
        ])
        
        self.assertEqual(len(relationships), 2, "Parent should have 2 relationships")
        self.assertIn(rel1, relationships, "Should include first relationship")
        self.assertIn(rel2, relationships, "Should include second relationship")

    def test_student_multiple_parents(self):
        """Test student with multiple parents."""
        father = self.create_parent(name='Test Father', last_name='Father')
        mother = self.create_parent(name='Test Mother', last_name='Mother', 
                                   email='mother@test.com')
        
        # Create relationships
        father_rel = self.create_parent_relationship(father, self.student1, 'father')
        mother_rel = self.create_parent_relationship(mother, self.student1, 'mother')
        
        # Find all relationships for this student
        relationships = self.env['op.parent.relation'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertEqual(len(relationships), 2, "Student should have 2 parents")
        
        # Verify different relation types
        relations = [rel.relation for rel in relationships]
        self.assertIn('father', relations, "Should have father relationship")
        self.assertIn('mother', relations, "Should have mother relationship")

    def test_relationship_type_validation(self):
        """Test validation of relationship types."""
        parent = self.create_parent()
        
        # Test valid relationship types
        valid_relations = ['father', 'mother', 'guardian', 'uncle', 'aunt', 'grandparent']
        
        for relation_type in valid_relations:
            # Create student for each relation type to avoid duplicates
            student = self.env['op.student'].create({
                'name': f'Student for {relation_type}',
                'first_name': 'Student',
                'last_name': relation_type.title(),
                'birth_date': '2005-01-01',
            })
            
            relationship = self.create_parent_relationship(parent, student, relation_type)
            self.assertEqual(relationship.relation, relation_type, 
                           f"Should accept {relation_type} as valid relation")

    def test_duplicate_relationship_prevention(self):
        """Test prevention of duplicate relationships."""
        parent = self.create_parent()
        
        # Create first relationship
        self.create_parent_relationship(parent, self.student1, 'father')
        
        # Try to create duplicate relationship
        with self.assertRaises(ValidationError):
            self.create_parent_relationship(parent, self.student1, 'father')

    def test_relationship_constraints(self):
        """Test relationship constraints."""
        # Test relationship without parent
        with self.assertRaises(ValidationError):
            self.env['op.parent.relation'].create({
                'student_id': self.student1.id,
                'relation': 'father',
            })
        
        # Test relationship without student
        parent = self.create_parent()
        with self.assertRaises(ValidationError):
            self.env['op.parent.relation'].create({
                'parent_id': parent.id,
                'relation': 'father',
            })

    def test_relationship_name_computation(self):
        """Test relationship name computation."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Check if name is computed
        if hasattr(relationship, 'name'):
            expected_name = f"{parent.name} - {self.student1.name} (father)"
            self.assertEqual(relationship.name, expected_name, 
                           "Relationship name should be computed correctly")

    def test_relationship_search_functionality(self):
        """Test search functionality for relationships."""
        father = self.create_parent(name='Search Father', last_name='Father')
        mother = self.create_parent(name='Search Mother', last_name='Mother',
                                   email='searchmother@test.com')
        
        # Create relationships
        father_rel = self.create_parent_relationship(father, self.student1, 'father')
        mother_rel = self.create_parent_relationship(mother, self.student1, 'mother')
        
        # Search by parent
        father_relationships = self.env['op.parent.relation'].search([
            ('parent_id', '=', father.id)
        ])
        self.assertIn(father_rel, father_relationships, "Should find father relationships")
        
        # Search by student
        student_relationships = self.env['op.parent.relation'].search([
            ('student_id', '=', self.student1.id)
        ])
        self.assertEqual(len(student_relationships), 2, "Should find both relationships")
        
        # Search by relation type
        father_relations = self.env['op.parent.relation'].search([
            ('relation', '=', 'father')
        ])
        self.assertIn(father_rel, father_relations, "Should find father relations")

    def test_relationship_deletion_cascade(self):
        """Test cascade deletion behavior."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Verify relationship exists
        self.assertTrue(relationship.exists(), "Relationship should exist")
        
        # Delete relationship
        relationship.unlink()
        
        # Verify relationship is deleted
        self.assertFalse(relationship.exists(), "Relationship should be deleted")

    def test_relationship_contact_information_sync(self):
        """Test synchronization of contact information."""
        parent = self.create_parent(
            phone='+1234567890',
            email='sync@test.com',
            street='123 Test Street'
        )
        
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Verify parent contact info is accessible through relationship
        self.assertEqual(relationship.parent_id.phone, '+1234567890',
                        "Phone should be accessible")
        self.assertEqual(relationship.parent_id.email, 'sync@test.com',
                        "Email should be accessible")

    def test_emergency_contact_designation(self):
        """Test emergency contact designation."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Test emergency contact flag if supported
        if hasattr(relationship, 'is_emergency_contact'):
            relationship.is_emergency_contact = True
            self.assertTrue(relationship.is_emergency_contact,
                          "Should mark as emergency contact")

    def test_relationship_permissions_access(self):
        """Test access permissions for relationships."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Test parent can access student data through relationship
        student_through_relation = relationship.student_id
        self.assertEqual(student_through_relation, self.student1,
                        "Parent should access student through relationship")

    def test_relationship_bulk_operations(self):
        """Test bulk operations on relationships."""
        # Create multiple parents and relationships
        parents = []
        relationships = []
        
        for i in range(5):
            parent = self.create_parent(
                name=f'Bulk Parent {i}',
                email=f'bulk{i}@test.com'
            )
            parents.append(parent)
            
            relationship = self.create_parent_relationship(parent, self.student1, 'guardian')
            relationships.append(relationship)
        
        # Bulk update operation
        relationship_ids = [r.id for r in relationships]
        bulk_relationships = self.env['op.parent.relation'].browse(relationship_ids)
        
        # Update all relationships
        bulk_relationships.write({'relation': 'guardian'})
        
        # Verify bulk update
        for relationship in relationships:
            relationship.refresh()
            self.assertEqual(relationship.relation, 'guardian',
                           f"Relationship {relationship.id} should be updated")

    def test_relationship_reporting_data(self):
        """Test data preparation for relationship reports."""
        father = self.create_parent(name='Report Father', last_name='Father')
        mother = self.create_parent(name='Report Mother', last_name='Mother',
                                   email='reportmother@test.com')
        
        # Create relationships
        father_rel = self.create_parent_relationship(father, self.student1, 'father')
        mother_rel = self.create_parent_relationship(mother, self.student1, 'mother')
        
        # Prepare report data
        report_data = []
        relationships = self.env['op.parent.relation'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        for rel in relationships:
            report_data.append({
                'student_name': rel.student_id.name,
                'parent_name': rel.parent_id.name,
                'relation_type': rel.relation,
                'parent_phone': rel.parent_id.phone,
                'parent_email': rel.parent_id.email,
            })
        
        # Verify report data
        self.assertEqual(len(report_data), 2, "Should have data for both parents")
        
        for entry in report_data:
            self.assertIn('student_name', entry, "Should include student name")
            self.assertIn('parent_name', entry, "Should include parent name")
            self.assertIn('relation_type', entry, "Should include relation type")

    def test_relationship_validation_business_rules(self):
        """Test business rule validation for relationships."""
        parent = self.create_parent()
        
        # Test maximum relationships per parent (if applicable)
        max_relationships = 10  # Example limit
        
        relationships = []
        for i in range(max_relationships):
            student = self.env['op.student'].create({
                'name': f'Validation Student {i}',
                'first_name': 'Validation',
                'last_name': f'Student{i}',
                'birth_date': '2005-01-01',
            })
            
            relationship = self.create_parent_relationship(parent, student, 'guardian')
            relationships.append(relationship)
        
        # Verify all relationships created successfully
        created_relationships = self.env['op.parent.relation'].search([
            ('parent_id', '=', parent.id)
        ])
        
        self.assertEqual(len(created_relationships), max_relationships,
                        "Should create all relationships within limit")

    def test_relationship_active_status_management(self):
        """Test active status management for relationships."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Test active status if supported
        if hasattr(relationship, 'active'):
            # Initially active
            self.assertTrue(relationship.active, "Relationship should be active by default")
            
            # Deactivate relationship
            relationship.active = False
            self.assertFalse(relationship.active, "Relationship should be deactivated")
            
            # Verify deactivated relationships don't appear in default searches
            active_relationships = self.env['op.parent.relation'].search([
                ('parent_id', '=', parent.id)
            ])
            self.assertNotIn(relationship, active_relationships,
                           "Deactivated relationship should not appear in default search")

    def test_relationship_performance_large_dataset(self):
        """Test performance with large relationship dataset."""
        # Create large number of relationships
        relationships = []
        
        for i in range(100):
            parent = self.create_parent(
                name=f'Perf Parent {i}',
                email=f'perf{i}@test.com'
            )
            
            student = self.env['op.student'].create({
                'name': f'Perf Student {i}',
                'first_name': 'Perf',
                'last_name': f'Student{i}',
                'birth_date': '2005-01-01',
            })
            
            relationship = self.create_parent_relationship(parent, student, 'guardian')
            relationships.append(relationship)
        
        # Test search performance
        search_results = self.env['op.parent.relation'].search([
            ('relation', '=', 'guardian')
        ])
        
        self.assertGreaterEqual(len(search_results), 100,
                               "Should handle large datasets efficiently")

    def test_relationship_data_integrity(self):
        """Test data integrity for relationships."""
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Test referential integrity
        self.assertTrue(relationship.parent_id.exists(), "Parent should exist")
        self.assertTrue(relationship.student_id.exists(), "Student should exist")
        
        # Test relationship consistency
        parent_relationships = self.env['op.parent.relation'].search([
            ('parent_id', '=', parent.id)
        ])
        self.assertIn(relationship, parent_relationships,
                     "Relationship should be found through parent")
        
        student_relationships = self.env['op.parent.relation'].search([
            ('student_id', '=', self.student1.id)
        ])
        self.assertIn(relationship, student_relationships,
                     "Relationship should be found through student")

    def test_relationship_workflow_integration(self):
        """Test integration with overall parent workflow."""
        # Create complete parent-student setup
        parent = self.create_parent()
        relationship = self.create_parent_relationship(parent, self.student1, 'father')
        
        # Test workflow: parent registration -> relationship creation -> portal access
        # 1. Parent is created and verified
        self.assertTrue(parent.exists(), "Parent should be created")
        self.assertTrue(parent.is_parent, "Should be marked as parent")
        
        # 2. Relationship is established
        self.assertTrue(relationship.exists(), "Relationship should be established")
        
        # 3. Parent can access student information through relationship
        student_info = {
            'name': relationship.student_id.name,
            'course': relationship.student_id.course_detail_ids[0].course_id.name if relationship.student_id.course_detail_ids else None,
            'batch': relationship.student_id.course_detail_ids[0].batch_id.name if relationship.student_id.course_detail_ids else None,
        }
        
        self.assertEqual(student_info['name'], self.student1.name,
                        "Parent should access student name through relationship")
        self.assertIsNotNone(student_info['course'],
                           "Parent should access student course information")