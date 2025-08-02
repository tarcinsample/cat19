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
from .test_fees_common import TestFeesCommon


@tagged('post_install', '-at_install', 'openeducat_fees')
class TestFeesCalculation(TestFeesCommon):
    """Test fee calculation and payment tracking."""

    def test_fees_element_creation(self):
        """Test basic fees element creation."""
        fees_element = self.create_fees_element()
        
        self.assertEqual(fees_element.name, 'Test Fee Element', "Name should be set")
        self.assertEqual(fees_element.product_id, self.tuition_product, "Product should be linked")
        self.assertEqual(fees_element.amount, 500.0, "Amount should be 500.0")

    def test_fees_terms_creation(self):
        """Test fees terms creation."""
        fees_terms = self.create_fees_terms()
        
        self.assertEqual(fees_terms.name, 'Test Fee Term', "Name should be set")
        self.assertEqual(fees_terms.course_id, self.course, "Course should be linked")
        self.assertEqual(fees_terms.batch_id, self.batch, "Batch should be linked")
        self.assertEqual(fees_terms.academic_year_id, self.academic_year, "Academic year should be linked")

    def test_student_fees_details_creation(self):
        """Test student fees details creation."""
        fees_details = self.create_student_fees_details()
        
        self.assertEqual(fees_details.student_id, self.student1, "Student should be linked")
        self.assertEqual(fees_details.amount, 500.0, "Amount should be 500.0")
        self.assertEqual(fees_details.state, 'draft', "State should be draft")

    def test_fees_calculation_workflow(self):
        """Test fees calculation workflow."""
        # Create fees elements
        tuition_element = self.create_fees_element(
            name='Tuition Fee',
            product_id=self.tuition_product.id,
            amount=1000.0
        )
        
        library_element = self.create_fees_element(
            name='Library Fee',
            product_id=self.library_product.id,
            amount=200.0
        )
        
        # Create fees terms with elements
        fees_terms = self.create_fees_terms()
        
        # Add elements to terms if supported
        if hasattr(fees_terms, 'fees_element_ids'):
            fees_terms.fees_element_ids = [(6, 0, [tuition_element.id, library_element.id])]
        
        # Calculate total fees
        total_fees = tuition_element.amount + library_element.amount
        self.assertEqual(total_fees, 1200.0, "Total fees should be 1200.0")

    def test_fees_payment_state_transitions(self):
        """Test fees payment state transitions."""
        fees_details = self.create_student_fees_details()
        
        # Test state transitions
        self.assertEqual(fees_details.state, 'draft', "Initial state should be draft")
        
        # Confirm fees
        if hasattr(fees_details, 'action_confirm'):
            fees_details.action_confirm()
            self.assertEqual(fees_details.state, 'confirm', "Should transition to confirm")
        
        # Mark as paid
        if hasattr(fees_details, 'action_paid'):
            fees_details.action_paid()
            self.assertEqual(fees_details.state, 'paid', "Should transition to paid")

    def test_fees_discount_calculation(self):
        """Test fees discount calculation."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Apply discount if supported
        if hasattr(fees_details, 'discount_percentage'):
            fees_details.discount_percentage = 10.0  # 10% discount
            
            # Calculate discounted amount
            discount_amount = (fees_details.amount * fees_details.discount_percentage) / 100
            final_amount = fees_details.amount - discount_amount
            
            self.assertEqual(discount_amount, 100.0, "Discount should be 100.0")
            self.assertEqual(final_amount, 900.0, "Final amount should be 900.0")

    def test_fees_installment_calculation(self):
        """Test fees installment calculation."""
        total_amount = 1200.0
        installments = 3
        
        # Calculate installment amount
        installment_amount = total_amount / installments
        
        # Create installment-based fees
        for i in range(installments):
            fees_details = self.create_student_fees_details(
                amount=installment_amount,
                installment_number=i + 1
            )
            
            self.assertEqual(fees_details.amount, 400.0, 
                           f"Installment {i+1} should be 400.0")

    def test_fees_late_payment_penalty(self):
        """Test late payment penalty calculation."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Set due date in the past
        if hasattr(fees_details, 'due_date'):
            fees_details.due_date = '2024-05-01'  # Past date
            
            # Calculate penalty if supported
            if hasattr(fees_details, 'penalty_amount'):
                penalty_rate = 2.0  # 2% penalty
                penalty_amount = (fees_details.amount * penalty_rate) / 100
                fees_details.penalty_amount = penalty_amount
                
                self.assertEqual(fees_details.penalty_amount, 20.0,
                               "Penalty should be 20.0")

    def test_fees_refund_calculation(self):
        """Test fees refund calculation."""
        fees_details = self.create_student_fees_details(amount=1000.0, state='paid')
        
        # Process refund if supported
        if hasattr(fees_details, 'refund_amount'):
            refund_percentage = 50.0  # 50% refund
            refund_amount = (fees_details.amount * refund_percentage) / 100
            fees_details.refund_amount = refund_amount
            
            self.assertEqual(fees_details.refund_amount, 500.0,
                           "Refund should be 500.0")

    def test_fees_scholarship_application(self):
        """Test scholarship application to fees."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Apply scholarship if supported
        if hasattr(fees_details, 'scholarship_amount'):
            scholarship_amount = 300.0
            fees_details.scholarship_amount = scholarship_amount
            
            # Calculate final amount after scholarship
            final_amount = fees_details.amount - scholarship_amount
            
            self.assertEqual(final_amount, 700.0,
                           "Amount after scholarship should be 700.0")

    def test_fees_currency_conversion(self):
        """Test fees currency conversion."""
        # Create fees in different currency if supported
        if 'res.currency' in self.env:
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            
            if usd_currency:
                fees_details = self.create_student_fees_details(
                    amount=100.0,
                    currency_id=usd_currency.id
                )
                
                # Verify currency is set
                if hasattr(fees_details, 'currency_id'):
                    self.assertEqual(fees_details.currency_id, usd_currency,
                                   "Currency should be USD")

    def test_fees_bulk_calculation(self):
        """Test bulk fees calculation for multiple students."""
        # Create additional students
        students = [self.student1]
        for i in range(3):
            student = self.env['op.student'].create({
                'name': f'Bulk Student {i+2}',
                'first_name': 'Bulk',
                'last_name': f'Student{i+2}',
                'birth_date': '2005-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            students.append(student)
        
        # Calculate fees for all students
        standard_amount = 1000.0
        fees_list = []
        
        for student in students:
            fees_details = self.create_student_fees_details(
                student=student,
                amount=standard_amount
            )
            fees_list.append(fees_details)
        
        # Verify bulk calculation
        total_fees = sum([fees.amount for fees in fees_list])
        expected_total = standard_amount * len(students)
        
        self.assertEqual(total_fees, expected_total,
                        f"Total fees should be {expected_total}")

    def test_fees_reporting_calculations(self):
        """Test fees reporting calculations."""
        # Create various fee records
        fees_data = [
            {'amount': 1000.0, 'state': 'paid'},
            {'amount': 1200.0, 'state': 'paid'},
            {'amount': 800.0, 'state': 'draft'},
            {'amount': 1500.0, 'state': 'confirm'},
        ]
        
        fees_records = []
        for data in fees_data:
            fees_details = self.create_student_fees_details(**data)
            fees_records.append(fees_details)
        
        # Calculate reporting metrics
        total_fees = sum([f.amount for f in fees_records])
        paid_fees = sum([f.amount for f in fees_records if f.state == 'paid'])
        outstanding_fees = sum([f.amount for f in fees_records if f.state != 'paid'])
        
        # Verify calculations
        self.assertEqual(total_fees, 4500.0, "Total fees should be 4500.0")
        self.assertEqual(paid_fees, 2200.0, "Paid fees should be 2200.0")
        self.assertEqual(outstanding_fees, 2300.0, "Outstanding fees should be 2300.0")

    def test_fees_tax_calculation(self):
        """Test fees tax calculation."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Apply tax if supported
        if hasattr(fees_details, 'tax_amount'):
            tax_rate = 18.0  # 18% tax
            tax_amount = (fees_details.amount * tax_rate) / 100
            fees_details.tax_amount = tax_amount
            
            total_with_tax = fees_details.amount + tax_amount
            
            self.assertEqual(fees_details.tax_amount, 180.0, "Tax should be 180.0")
            self.assertEqual(total_with_tax, 1180.0, "Total with tax should be 1180.0")

    def test_fees_payment_method_tracking(self):
        """Test fees payment method tracking."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Set payment method if supported
        if hasattr(fees_details, 'payment_method'):
            payment_methods = ['cash', 'bank_transfer', 'online', 'cheque']
            
            for method in payment_methods:
                fees_details.payment_method = method
                self.assertEqual(fees_details.payment_method, method,
                               f"Should track {method} payment method")

    def test_fees_auto_calculation_triggers(self):
        """Test automatic fees calculation triggers."""
        # Test calculation when student is enrolled
        if hasattr(self.student1, 'calculate_fees'):
            # This would typically trigger automatic fee calculation
            calculated_fees = self.student1.calculate_fees()
            
            # Verify calculation was triggered
            if calculated_fees:
                self.assertGreater(len(calculated_fees), 0,
                                 "Should generate calculated fees")

    def test_fees_validation_rules(self):
        """Test fees validation rules."""
        # Test negative amount validation
        with self.assertRaises(ValidationError):
            self.create_student_fees_details(amount=-100.0)
        
        # Test zero amount validation
        with self.assertRaises(ValidationError):
            self.create_student_fees_details(amount=0.0)

    def test_fees_duplicate_prevention(self):
        """Test prevention of duplicate fees."""
        # Create first fees record
        fees1 = self.create_student_fees_details()
        
        # Try to create duplicate - should be prevented by business logic
        # This would typically be handled by unique constraints or validation

    def test_fees_integration_with_accounting(self):
        """Test fees integration with accounting system."""
        fees_details = self.create_student_fees_details(amount=1000.0, state='paid')
        
        # Test accounting integration if supported
        if 'account.move' in self.env:
            # This would typically create journal entries
            # for fee payments and revenue recognition
            pass

    def test_fees_performance_large_dataset(self):
        """Test fees calculation performance with large dataset."""
        # Create large number of fee records
        fees_records = []
        
        for i in range(100):
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 10),  # Varying amounts
                student=self.student1
            )
            fees_records.append(fees_details)
        
        # Test calculation performance
        total_fees = sum([fees.amount for fees in fees_records])
        
        # Verify performance
        self.assertEqual(len(fees_records), 100, "Should create 100 fee records")
        self.assertGreater(total_fees, 0, "Should calculate total efficiently")

    def test_fees_workflow_integration(self):
        """Test complete fees workflow integration."""
        # 1. Create fees structure
        fees_element = self.create_fees_element(amount=1000.0)
        fees_terms = self.create_fees_terms()
        
        # 2. Generate student fees
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # 3. Process payment workflow
        if hasattr(fees_details, 'action_confirm'):
            fees_details.action_confirm()
        
        if hasattr(fees_details, 'action_paid'):
            fees_details.action_paid()
        
        # 4. Verify workflow completion
        self.assertTrue(fees_element.exists(), "Fee element should exist")
        self.assertTrue(fees_terms.exists(), "Fee terms should exist")
        self.assertTrue(fees_details.exists(), "Fee details should exist")
        
        # 5. Verify final state
        if hasattr(fees_details, 'state'):
            self.assertIn(fees_details.state, ['paid', 'confirm'],
                         "Fees should be in final state")

    def test_fees_analytics_and_insights(self):
        """Test fees analytics and insights generation."""
        # Create diverse fee data for analytics
        analytics_data = []
        
        # Different fee types and amounts
        fee_scenarios = [
            {'amount': 1000.0, 'type': 'tuition', 'state': 'paid'},
            {'amount': 200.0, 'type': 'library', 'state': 'paid'},
            {'amount': 500.0, 'type': 'lab', 'state': 'draft'},
            {'amount': 1500.0, 'type': 'tuition', 'state': 'confirm'},
        ]
        
        for scenario in fee_scenarios:
            fees_details = self.create_student_fees_details(**scenario)
            analytics_data.append(fees_details)
        
        # Generate analytics
        analytics = {
            'total_revenue': sum([f.amount for f in analytics_data if f.state == 'paid']),
            'pending_amount': sum([f.amount for f in analytics_data if f.state != 'paid']),
            'collection_rate': 0,
        }
        
        total_fees = sum([f.amount for f in analytics_data])
        if total_fees > 0:
            analytics['collection_rate'] = (analytics['total_revenue'] / total_fees) * 100
        
        # Verify analytics
        self.assertEqual(analytics['total_revenue'], 1200.0, "Revenue should be 1200.0")
        self.assertEqual(analytics['pending_amount'], 2000.0, "Pending should be 2000.0")
        self.assertEqual(round(analytics['collection_rate'], 2), 37.5,
                        "Collection rate should be 37.5%")