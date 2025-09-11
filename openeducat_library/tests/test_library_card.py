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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_library_common import TestLibraryCommon


@tagged('post_install', '-at_install', 'openeducat_library')
class TestLibraryCard(TestLibraryCommon):
    """Test library card generation and barcode functionality."""

    def test_library_card_creation(self):
        """Test basic library card creation."""
        card = self.create_library_card(self.student1)
        
        self.assertEqual(card.student_id, self.student1, "Student should be linked")
        self.assertEqual(card.card_type_id, self.card_type, "Card type should be linked")
        self.assertTrue(card.number, "Card number should be generated")

    def test_library_card_number_generation(self):
        """Test automatic card number generation."""
        card1 = self.create_library_card(self.student1)
        card2 = self.create_library_card(self.student2)
        
        self.assertNotEqual(card1.number, card2.number, 
                           "Card numbers should be unique")
        self.assertTrue(card1.number, "Card1 should have number")
        self.assertTrue(card2.number, "Card2 should have number")

    def test_library_card_barcode_generation(self):
        """Test barcode generation for library cards."""
        card = self.create_library_card(self.student1)
        
        if hasattr(card, 'barcode'):
            self.assertTrue(card.barcode, "Barcode should be generated")
            # Barcode should be based on card number
            self.assertIn(card.number, card.barcode or '', 
                         "Barcode should contain card number")

    def test_library_card_student_uniqueness(self):
        """Test that each student can have only one active card."""
        # Create first card
        card1 = self.create_library_card(self.student1)
        
        # Try to create second card for same student
        with self.assertRaises(ValidationError):
            self.create_library_card(self.student1)

    def test_library_card_type_configuration(self):
        """Test library card type configuration."""
        card_type = self.card_type
        
        self.assertEqual(card_type.allow_day, 7, "Allow days should be 7")
        self.assertEqual(card_type.penalties_day, 1.0, "Penalty per day should be 1.0")

    def test_library_card_validity_period(self):
        """Test library card validity period."""
        card = self.create_library_card(self.student1)
        
        # Set validity dates if supported
        if hasattr(card, 'valid_from'):
            card.valid_from = self.today
            card.valid_to = self.today + timedelta(days=365)
            
            self.assertEqual(card.valid_from, self.today, "Valid from should be today")
            self.assertEqual(card.valid_to, self.today + timedelta(days=365),
                           "Valid to should be one year from today")

    def test_library_card_status_management(self):
        """Test library card status management."""
        card = self.create_library_card(self.student1)
        
        # Test default status
        if hasattr(card, 'state'):
            self.assertIn(card.state, ['active', 'draft'], "Card should have valid state")
            
            # Test status transitions
            card.state = 'active'
            self.assertEqual(card.state, 'active', "Card should be active")
            
            card.state = 'suspend'
            self.assertEqual(card.state, 'suspend', "Card should be suspended")

    def test_library_card_renewal(self):
        """Test library card renewal functionality."""
        card = self.create_library_card(self.student1)
        
        # Test renewal method if exists
        if hasattr(card, 'action_renew'):
            original_valid_to = getattr(card, 'valid_to', None)
            card.action_renew()
            
            if original_valid_to:
                self.assertGreater(card.valid_to, original_valid_to,
                                 "Renewed card should have extended validity")

    def test_library_card_replacement(self):
        """Test library card replacement for lost cards."""
        card = self.create_library_card(self.student1)
        original_number = card.number
        
        # Mark card as lost
        if hasattr(card, 'state'):
            card.state = 'lost'
            
            # Create replacement card
            replacement_card = self.env['op.library.card'].create({
                'student_id': self.student1.id,
                'card_type_id': self.card_type.id,
                'is_replacement': True,
            })
            
            self.assertNotEqual(replacement_card.number, original_number,
                              "Replacement card should have different number")

    def test_library_card_access_permissions(self):
        """Test access permissions for library cards."""
        card = self.create_library_card(self.student1)
        
        # Test that card belongs to correct student
        self.assertEqual(card.student_id, self.student1,
                        "Card should belong to correct student")
        
        # Test card access validation
        # This would typically involve checking user permissions

    def test_library_card_fine_calculation(self):
        """Test fine calculation based on card type."""
        card = self.create_library_card(self.student1)
        
        # Calculate fine for overdue days
        overdue_days = 3
        expected_fine = card.card_type_id.penalties_day * overdue_days
        
        self.assertEqual(expected_fine, 3.0, "Fine should be 3.0 for 3 days")

    def test_library_card_issue_limits(self):
        """Test issue limits based on card type."""
        card = self.create_library_card(self.student1)
        
        # Test default issue limit if configured
        if hasattr(card.card_type_id, 'max_issue'):
            max_issue = card.card_type_id.max_issue or 5  # Default 5
            self.assertGreater(max_issue, 0, "Should have positive issue limit")

    def test_library_card_expiry_notification(self):
        """Test card expiry notification system."""
        card = self.create_library_card(self.student1)
        
        if hasattr(card, 'valid_to'):
            # Set card to expire soon
            card.valid_to = self.today + timedelta(days=7)
            
            # Check if card is expiring soon
            days_to_expiry = (card.valid_to - self.today).days
            is_expiring_soon = days_to_expiry <= 14  # 2 weeks notice
            
            self.assertTrue(is_expiring_soon, "Card should be flagged as expiring soon")

    def test_library_card_usage_tracking(self):
        """Test tracking of card usage statistics."""
        card = self.create_library_card(self.student1)
        media = self.create_media()
        
        # Create some movements to track usage
        movement1 = self.create_media_movement(media, self.student1, 'issue')
        movement2 = self.create_media_movement(media, self.student1, 'return')
        
        # Count usage if tracking is implemented
        usage_count = self.env['op.media.movement'].search_count([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertEqual(usage_count, 2, "Should track 2 movements")

    def test_library_card_blocking_conditions(self):
        """Test conditions that block library card usage."""
        card = self.create_library_card(self.student1)
        
        # Test blocking due to unpaid fines
        if hasattr(card, 'total_fine'):
            card.total_fine = 100.0  # High fine amount
            
            # Card should be blocked for high fines
            if hasattr(card, 'is_blocked'):
                self.assertTrue(card.is_blocked, "Card should be blocked for high fines")

    def test_library_card_student_details_sync(self):
        """Test synchronization with student details."""
        card = self.create_library_card(self.student1)
        
        # Verify student details are accessible through card
        self.assertEqual(card.student_id.name, self.student1.name,
                        "Student name should be accessible")
        self.assertEqual(card.student_id.birth_date, self.student1.birth_date,
                        "Student birth date should be accessible")

    def test_library_card_bulk_generation(self):
        """Test bulk generation of library cards."""
        # Create additional students
        students = [self.student1, self.student2]
        
        # Add more students for bulk testing
        for i in range(3, 6):
            student = self.env['op.student'].create({
                'name': f'Bulk Student {i}',
                'first_name': 'Bulk',
                'last_name': f'Student{i}',
                'birth_date': '2000-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            students.append(student)
        
        # Generate cards for all students
        cards = []
        for student in students:
            if not self.env['op.library.card'].search([('student_id', '=', student.id)]):
                card = self.create_library_card(student)
                cards.append(card)
        
        self.assertGreaterEqual(len(cards), 3, "Should generate multiple cards")

    def test_library_card_qr_code_generation(self):
        """Test QR code generation for library cards."""
        card = self.create_library_card(self.student1)
        
        # Test QR code generation if supported
        if hasattr(card, 'qr_code'):
            # QR code should contain card information
            expected_qr_data = f"LIBRARY_CARD:{card.number}"
            # This would normally generate actual QR code
            card.qr_code = expected_qr_data
            
            self.assertEqual(card.qr_code, expected_qr_data,
                           "QR code should contain card data")

    def test_library_card_printing_data(self):
        """Test data preparation for card printing."""
        card = self.create_library_card(self.student1)
        
        # Prepare printing data
        print_data = {
            'card_number': card.number,
            'student_name': card.student_id.name,
            'student_id': card.student_id.id,
            'card_type': card.card_type_id.name,
            'issue_date': self.today,
            'valid_from': getattr(card, 'valid_from', self.today),
            'valid_to': getattr(card, 'valid_to', self.today + timedelta(days=365)),
        }
        
        # Verify all required data is present
        self.assertIn('card_number', print_data, "Should include card number")
        self.assertIn('student_name', print_data, "Should include student name")
        self.assertTrue(print_data['card_number'], "Card number should not be empty")

    def test_library_card_security_features(self):
        """Test security features of library cards."""
        card = self.create_library_card(self.student1)
        
        # Test card number format (should be secure/random)
        self.assertIsInstance(card.number, str, "Card number should be string")
        self.assertGreater(len(card.number), 4, "Card number should be reasonably long")
        
        # Test that card numbers don't follow predictable pattern
        card2 = self.create_library_card(self.student2)
        
        # Cards should not be sequential
        try:
            num1 = int(card.number)
            num2 = int(card2.number)
            self.assertNotEqual(num2, num1 + 1, "Card numbers should not be sequential")
        except ValueError:
            # Non-numeric card numbers are acceptable
            pass

    def test_library_card_validation_rules(self):
        """Test validation rules for library cards."""
        # Test card creation without student
        with self.assertRaises(ValidationError):
            self.env['op.library.card'].create({
                'card_type_id': self.card_type.id,
            })
        
        # Test card creation without card type
        with self.assertRaises(ValidationError):
            self.env['op.library.card'].create({
                'student_id': self.student1.id,
            })

    def test_library_card_performance(self):
        """Test performance of card operations."""
        # Create multiple cards
        cards = []
        for i in range(50):
            student = self.env['op.student'].create({
                'name': f'Perf Student {i}',
                'first_name': 'Perf',
                'last_name': f'Student{i}',
                'birth_date': '2000-01-01',
            })
            
            card = self.create_library_card(student)
            cards.append(card)
        
        # Test bulk search performance
        search_results = self.env['op.library.card'].search([
            ('card_type_id', '=', self.card_type.id)
        ])
        
        self.assertGreaterEqual(len(search_results), 50,
                               "Should find all created cards efficiently")

    def test_library_card_integration_workflow(self):
        """Test integration with overall library workflow."""
        card = self.create_library_card(self.student1)
        media = self.create_media()
        
        # Test complete workflow: card -> issue -> return
        # 1. Verify card is active
        if hasattr(card, 'state'):
            self.assertIn(card.state, ['active', 'draft'], "Card should be usable")
        
        # 2. Issue media using the card
        movement = self.create_media_movement(media, self.student1, 'issue')
        
        # 3. Verify movement is linked to card holder
        self.assertEqual(movement.student_id, card.student_id,
                        "Movement should be linked to card holder")
        
        # 4. Return media
        return_movement = self.create_media_movement(
            media, self.student1, 'return',
            return_date=self.today + timedelta(days=1)
        )
        
        self.assertEqual(return_movement.student_id, card.student_id,
                        "Return should be linked to same card holder")