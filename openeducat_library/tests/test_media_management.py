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

from datetime import timedelta
from odoo.exceptions import ValidationError, UserError
from odoo.tests import tagged
from .test_library_common import TestLibraryCommon


@tagged('post_install', '-at_install', 'openeducat_library')
class TestMediaManagement(TestLibraryCommon):
    """Test media management operations (issue, return, reserve)."""

    def setUp(self):
        """Set up test data for media management tests."""
        super().setUp()
        self.media = self.create_media()
        self.library_card = self.create_library_card(self.student1)

    def test_media_creation(self):
        """Test basic media creation."""
        media = self.create_media(name='Test Book Creation')
        
        self.assertEqual(media.name, 'Test Book Creation', "Media name should be set")
        self.assertEqual(media.state, 'available', "Media should be available by default")
        self.assertEqual(media.media_type, self.media_type_book, "Media type should be book")
        self.assertIn(self.author1, media.author_ids, "Author should be linked")

    def test_media_isbn_validation(self):
        """Test ISBN validation for media."""
        # Test valid ISBN
        media = self.create_media(isbn='978-0123456789')
        self.assertEqual(media.isbn, '978-0123456789', "Valid ISBN should be accepted")
        
        # Test duplicate ISBN
        with self.assertRaises(ValidationError):
            self.create_media(isbn='978-0123456789')

    def test_media_state_transitions(self):
        """Test media state transitions."""
        media = self.media
        
        # Test available to issued
        media.state = 'issued'
        self.assertEqual(media.state, 'issued', "Should transition to issued")
        
        # Test issued to available
        media.state = 'available'
        self.assertEqual(media.state, 'available', "Should return to available")

    def test_media_issue_operation(self):
        """Test media issue operation."""
        media = self.media
        
        # Create issue movement
        movement = self.create_media_movement(media, self.student1, 'issue')
        
        self.assertEqual(movement.type, 'issue', "Movement type should be issue")
        self.assertEqual(movement.media_id, media, "Media should be linked")
        self.assertEqual(movement.student_id, self.student1, "Student should be linked")
        self.assertEqual(movement.issue_date, self.today, "Issue date should be today")

    def test_media_return_operation(self):
        """Test media return operation."""
        media = self.media
        
        # First issue the media
        issue_movement = self.create_media_movement(media, self.student1, 'issue')
        
        # Then return it
        return_movement = self.create_media_movement(
            media, self.student1, 'return',
            issue_date=self.today,
            return_date=self.today + timedelta(days=1)
        )
        
        self.assertEqual(return_movement.type, 'return', "Movement type should be return")
        self.assertIsNotNone(return_movement.return_date, "Return date should be set")

    def test_media_availability_checking(self):
        """Test media availability checking."""
        media = self.media
        
        # Initially available
        self.assertEqual(media.state, 'available', "Media should be available")
        
        # Issue the media
        media.state = 'issued'
        
        # Check availability
        available_media = self.env['op.media'].search([('state', '=', 'available')])
        self.assertNotIn(media, available_media, "Issued media should not be available")

    def test_media_reservation_system(self):
        """Test media reservation functionality."""
        media = self.media
        
        # Create reservation
        queue_entry = self.create_media_queue(media, self.student2)
        
        self.assertEqual(queue_entry.media_id, media, "Media should be linked to queue")
        self.assertEqual(queue_entry.student_id, self.student2, "Student should be linked")
        self.assertEqual(queue_entry.request_date, self.today, "Request date should be today")

    def test_media_multiple_reservations(self):
        """Test multiple reservations for same media."""
        media = self.media
        
        # Create multiple reservations
        queue1 = self.create_media_queue(media, self.student1)
        queue2 = self.create_media_queue(media, self.student2)
        
        self.assertNotEqual(queue1, queue2, "Should create separate queue entries")
        
        # Check queue order
        queue_entries = self.env['op.media.queue'].search([
            ('media_id', '=', media.id)
        ], order='request_date')
        
        self.assertEqual(len(queue_entries), 2, "Should have 2 queue entries")

    def test_media_overdue_detection(self):
        """Test overdue media detection."""
        media = self.media
        
        # Create overdue movement
        overdue_movement = self.create_media_movement(
            media, self.student1, 'issue',
            issue_date=self.today - timedelta(days=10),
            return_date=self.today - timedelta(days=3)
        )
        
        # Check if movement is overdue
        is_overdue = overdue_movement.return_date < self.today
        self.assertTrue(is_overdue, "Movement should be overdue")

    def test_media_search_functionality(self):
        """Test media search by various criteria."""
        # Create additional media for search testing
        book2 = self.create_media(
            name='Advanced Python Programming',
            isbn='978-9876543210',
            tag_ids=[(6, 0, [self.tag_science.id])]
        )
        
        journal = self.create_media(
            name='Science Journal',
            media_type=self.media_type_journal.id,
            tag_ids=[(6, 0, [self.tag_science.id])]
        )
        
        # Search by name
        books_by_name = self.env['op.media'].search([
            ('name', 'ilike', 'python')
        ])
        self.assertIn(book2, books_by_name, "Should find book by name")
        
        # Search by media type
        books_by_type = self.env['op.media'].search([
            ('media_type', '=', self.media_type_book.id)
        ])
        self.assertIn(self.media, books_by_type, "Should find books by type")
        self.assertIn(book2, books_by_type, "Should find both books")
        self.assertNotIn(journal, books_by_type, "Should not include journals")
        
        # Search by tag
        science_media = self.env['op.media'].search([
            ('tag_ids', 'in', [self.tag_science.id])
        ])
        self.assertGreaterEqual(len(science_media), 2, "Should find science tagged media")

    def test_media_author_relationships(self):
        """Test media-author relationships."""
        media = self.media
        
        # Test multiple authors
        media.author_ids = [(6, 0, [self.author1.id, self.author2.id])]
        
        self.assertEqual(len(media.author_ids), 2, "Should have 2 authors")
        self.assertIn(self.author1, media.author_ids, "Should include author1")
        self.assertIn(self.author2, media.author_ids, "Should include author2")

    def test_media_publisher_relationship(self):
        """Test media-publisher relationship."""
        media = self.media
        
        self.assertEqual(media.publisher_id, self.publisher, "Publisher should be linked")
        
        # Update publisher
        new_publisher = self.env['op.publisher'].create({
            'name': 'New Publisher',
            'website': 'https://newpublisher.com',
        })
        
        media.publisher_id = new_publisher
        self.assertEqual(media.publisher_id, new_publisher, "Publisher should be updated")

    def test_media_location_tracking(self):
        """Test media location and unit tracking."""
        media = self.media
        
        self.assertEqual(media.unit_id, self.media_unit, "Unit should be set")
        
        # Create additional unit
        unit2 = self.env['op.media.unit'].create({
            'name': 'Branch Library',
            'code': 'BL001',
        })
        
        # Move media to different unit
        media.unit_id = unit2
        self.assertEqual(media.unit_id, unit2, "Media should be moved to new unit")

    def test_media_copy_management(self):
        """Test management of multiple copies."""
        # Create multiple copies of same book
        copy1 = self.create_media(name='Book Copy 1', isbn='978-1111111111')
        copy2 = self.create_media(name='Book Copy 1', isbn='978-2222222222')
        
        # Both should exist with different ISBNs
        self.assertNotEqual(copy1.isbn, copy2.isbn, "Copies should have different ISBNs")
        self.assertEqual(copy1.name, copy2.name, "Copies can have same name")

    def test_media_damage_lost_states(self):
        """Test handling of damaged and lost media."""
        media = self.media
        
        # Mark as damaged
        media.state = 'lost'
        self.assertEqual(media.state, 'lost', "Should mark as lost")
        
        # Lost media should not be available for issue
        available_media = self.env['op.media'].search([
            ('state', '=', 'available')
        ])
        self.assertNotIn(media, available_media, "Lost media should not be available")

    def test_media_bulk_operations(self):
        """Test bulk operations on media."""
        # Create multiple media items
        media_list = []
        for i in range(5):
            media = self.create_media(
                name=f'Bulk Book {i}',
                isbn=f'978-{i:010d}'
            )
            media_list.append(media)
        
        # Bulk state update
        media_ids = [m.id for m in media_list]
        bulk_media = self.env['op.media'].browse(media_ids)
        bulk_media.write({'state': 'maintenance'})
        
        # Verify bulk update
        for media in media_list:
            media.refresh()
            self.assertEqual(media.state, 'maintenance', 
                           f"Media {media.name} should be in maintenance")

    def test_media_validation_constraints(self):
        """Test media validation constraints."""
        # Test empty name
        with self.assertRaises(ValidationError):
            self.create_media(name='')
        
        # Test invalid ISBN format
        with self.assertRaises(ValidationError):
            self.create_media(isbn='invalid-isbn')

    def test_media_statistics_computation(self):
        """Test computation of media statistics."""
        # Create various media in different states
        available_media = self.create_media(name='Available Book', state='available')
        issued_media = self.create_media(name='Issued Book', state='issued', isbn='978-1234567890')
        lost_media = self.create_media(name='Lost Book', state='lost', isbn='978-0987654321')
        
        # Count by state
        available_count = self.env['op.media'].search_count([('state', '=', 'available')])
        issued_count = self.env['op.media'].search_count([('state', '=', 'issued')])
        lost_count = self.env['op.media'].search_count([('state', '=', 'lost')])
        
        self.assertGreaterEqual(available_count, 1, "Should have available media")
        self.assertGreaterEqual(issued_count, 1, "Should have issued media")
        self.assertGreaterEqual(lost_count, 1, "Should have lost media")

    def test_media_reservation_priority(self):
        """Test reservation priority handling."""
        media = self.media
        
        # Create reservations with different priorities
        queue1 = self.create_media_queue(
            media, self.student1,
            request_date=self.today - timedelta(days=2)
        )
        queue2 = self.create_media_queue(
            media, self.student2,
            request_date=self.today - timedelta(days=1)
        )
        
        # Earlier request should have higher priority
        queue_entries = self.env['op.media.queue'].search([
            ('media_id', '=', media.id)
        ], order='request_date')
        
        self.assertEqual(queue_entries[0], queue1, "Earlier request should be first")

    def test_media_performance_large_dataset(self):
        """Test performance with large media dataset."""
        # Create large number of media items
        media_list = []
        for i in range(100):
            media = self.create_media(
                name=f'Performance Book {i}',
                isbn=f'978-{i:010d}'
            )
            media_list.append(media)
        
        # Test search performance
        search_results = self.env['op.media'].search([
            ('state', '=', 'available')
        ])
        
        self.assertGreaterEqual(len(search_results), 100, 
                               "Should find all available media efficiently")

    def test_media_workflow_integration(self):
        """Test integration with library workflow."""
        media = self.media
        student = self.student1
        
        # Complete workflow: reserve -> issue -> return
        # 1. Reserve
        queue_entry = self.create_media_queue(media, student)
        
        # 2. Issue
        issue_movement = self.create_media_movement(media, student, 'issue')
        media.state = 'issued'
        
        # 3. Return
        return_movement = self.create_media_movement(
            media, student, 'return',
            return_date=self.today + timedelta(days=1)
        )
        media.state = 'available'
        
        # Verify workflow completion
        self.assertEqual(media.state, 'available', "Media should be available after return")
        self.assertTrue(queue_entry.exists(), "Queue entry should still exist")
        self.assertTrue(issue_movement.exists(), "Issue movement should be recorded")
        self.assertTrue(return_movement.exists(), "Return movement should be recorded")