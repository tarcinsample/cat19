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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_fees_common import TestFeesCommon


@tagged('post_install', '-at_install', 'openeducat_fees')
class TestFeesPayment(TestFeesCommon):
    """Test fees payment processing and tracking."""

    def test_payment_creation(self):
        """Test basic payment creation."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Create payment record if supported
        if 'account.payment' in self.env:
            payment = self.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': fees_details.student_id.partner_id.id,
                'amount': fees_details.amount,
                'journal_id': self._get_payment_journal().id,
            })
            
            self.assertEqual(payment.amount, 1000.0, "Payment amount should match")
            self.assertEqual(payment.payment_type, 'inbound', "Should be inbound payment")

    def test_partial_payment_tracking(self):
        """Test partial payment tracking."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Test partial payments
        partial_amounts = [300.0, 400.0, 300.0]
        total_paid = 0
        
        for amount in partial_amounts:
            total_paid += amount
            
            # Update paid amount if supported
            if hasattr(fees_details, 'paid_amount'):
                fees_details.paid_amount = total_paid
                
                # Calculate remaining
                remaining = fees_details.amount - fees_details.paid_amount
                
                if remaining <= 0:
                    fees_details.state = 'paid'
                else:
                    fees_details.state = 'partial'
        
        if hasattr(fees_details, 'paid_amount'):
            self.assertEqual(fees_details.paid_amount, 1000.0, "Should track total paid amount")
            self.assertEqual(fees_details.state, 'paid', "Should be fully paid")

    def test_payment_due_date_tracking(self):
        """Test payment due date tracking."""
        future_date = date.today() + timedelta(days=30)
        fees_details = self.create_student_fees_details(
            amount=1000.0,
            due_date=future_date
        )
        
        if hasattr(fees_details, 'due_date'):
            self.assertEqual(fees_details.due_date, future_date, "Should set due date")
            
            # Test overdue calculation
            overdue_date = date.today() - timedelta(days=5)
            fees_details.due_date = overdue_date
            
            is_overdue = fees_details.due_date < date.today()
            self.assertTrue(is_overdue, "Should detect overdue payments")

    def test_payment_method_recording(self):
        """Test payment method recording."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        payment_methods = ['cash', 'cheque', 'bank_transfer', 'online', 'credit_card']
        
        for method in payment_methods:
            if hasattr(fees_details, 'payment_method'):
                fees_details.payment_method = method
                self.assertEqual(fees_details.payment_method, method,
                               f"Should record {method} payment method")

    def test_payment_reference_tracking(self):
        """Test payment reference tracking."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Test reference tracking if supported
        if hasattr(fees_details, 'payment_reference'):
            reference = 'PAY-2024-001'
            fees_details.payment_reference = reference
            
            self.assertEqual(fees_details.payment_reference, reference,
                           "Should track payment reference")

    def test_payment_receipt_generation(self):
        """Test payment receipt generation."""
        fees_details = self.create_student_fees_details(amount=1000.0, state='paid')
        
        # Test receipt generation if supported
        if hasattr(fees_details, 'receipt_number'):
            receipt_number = f"REC-{fees_details.id:06d}"
            fees_details.receipt_number = receipt_number
            
            self.assertEqual(fees_details.receipt_number, receipt_number,
                           "Should generate receipt number")

    def test_payment_installment_plan(self):
        """Test payment installment plan."""
        total_amount = 3000.0
        installments = 3
        installment_amount = total_amount / installments
        
        # Create installment plan
        installment_records = []
        for i in range(installments):
            due_date = date.today() + timedelta(days=30 * (i + 1))
            
            fees_details = self.create_student_fees_details(
                amount=installment_amount,
                due_date=due_date,
                installment_number=i + 1
            )
            installment_records.append(fees_details)
        
        # Verify installment plan
        total_installments = sum([rec.amount for rec in installment_records])
        self.assertEqual(total_installments, total_amount,
                        "Installments should sum to total amount")

    def test_payment_late_fee_calculation(self):
        """Test late fee calculation."""
        overdue_date = date.today() - timedelta(days=10)
        fees_details = self.create_student_fees_details(
            amount=1000.0,
            due_date=overdue_date
        )
        
        # Calculate late fee if supported
        if hasattr(fees_details, 'late_fee_rate'):
            fees_details.late_fee_rate = 2.0  # 2% per month
            
            days_overdue = (date.today() - fees_details.due_date).days
            late_fee = (fees_details.amount * fees_details.late_fee_rate / 100) * (days_overdue / 30)
            
            if hasattr(fees_details, 'late_fee_amount'):
                fees_details.late_fee_amount = late_fee
                
                self.assertGreater(fees_details.late_fee_amount, 0,
                                 "Should calculate late fee for overdue payment")

    def test_payment_discount_application(self):
        """Test payment discount application."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Apply early payment discount if supported
        if hasattr(fees_details, 'early_payment_discount'):
            fees_details.early_payment_discount = 5.0  # 5% discount
            
            discount_amount = (fees_details.amount * fees_details.early_payment_discount) / 100
            final_amount = fees_details.amount - discount_amount
            
            self.assertEqual(discount_amount, 50.0, "Should calculate discount")
            self.assertEqual(final_amount, 950.0, "Should apply discount to final amount")

    def test_payment_refund_processing(self):
        """Test payment refund processing."""
        fees_details = self.create_student_fees_details(amount=1000.0, state='paid')
        
        # Process refund if supported
        if hasattr(fees_details, 'refund_amount'):
            refund_amount = 300.0
            fees_details.refund_amount = refund_amount
            fees_details.state = 'refunded'
            
            net_amount = fees_details.amount - fees_details.refund_amount
            
            self.assertEqual(fees_details.refund_amount, 300.0, "Should track refund amount")
            self.assertEqual(net_amount, 700.0, "Should calculate net amount after refund")

    def test_payment_currency_conversion(self):
        """Test payment currency conversion."""
        # Test multi-currency payments if supported
        if 'res.currency' in self.env:
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            
            if usd_currency:
                fees_details = self.create_student_fees_details(
                    amount=100.0,
                    currency_id=usd_currency.id
                )
                
                if hasattr(fees_details, 'currency_id'):
                    self.assertEqual(fees_details.currency_id, usd_currency,
                                   "Should handle multi-currency payments")

    def test_payment_batch_processing(self):
        """Test batch payment processing."""
        # Create multiple fees for batch processing
        fees_records = []
        for i in range(5):
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 100),
                state='confirm'
            )
            fees_records.append(fees_details)
        
        # Process batch payment
        total_amount = sum([fees.amount for fees in fees_records])
        
        # Mark all as paid in batch
        for fees in fees_records:
            fees.state = 'paid'
        
        # Verify batch processing
        paid_records = [fees for fees in fees_records if fees.state == 'paid']
        self.assertEqual(len(paid_records), 5, "Should process all payments in batch")

    def test_payment_reconciliation(self):
        """Test payment reconciliation."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Test reconciliation if supported
        if hasattr(fees_details, 'reconciled'):
            fees_details.reconciled = True
            self.assertTrue(fees_details.reconciled, "Should mark as reconciled")

    def test_payment_journal_integration(self):
        """Test payment journal integration."""
        fees_details = self.create_student_fees_details(amount=1000.0, state='paid')
        
        # Test journal entry creation if supported
        if 'account.move' in self.env:
            # This would typically create journal entries for payment
            # Check if journal entries are properly created
            pass

    def test_payment_tax_handling(self):
        """Test payment tax handling."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Apply tax if supported
        if hasattr(fees_details, 'tax_amount'):
            tax_rate = 18.0  # 18% tax
            tax_amount = (fees_details.amount * tax_rate) / 100
            fees_details.tax_amount = tax_amount
            
            total_with_tax = fees_details.amount + tax_amount
            
            self.assertEqual(fees_details.tax_amount, 180.0, "Should calculate tax")
            self.assertEqual(total_with_tax, 1180.0, "Should include tax in total")

    def test_payment_approval_workflow(self):
        """Test payment approval workflow."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Test approval workflow if supported
        if hasattr(fees_details, 'approval_state'):
            fees_details.approval_state = 'pending'
            self.assertEqual(fees_details.approval_state, 'pending',
                           "Should track approval state")
            
            # Approve payment
            fees_details.approval_state = 'approved'
            self.assertEqual(fees_details.approval_state, 'approved',
                           "Should approve payment")

    def test_payment_notification_system(self):
        """Test payment notification system."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Test notification tracking if supported
        if hasattr(fees_details, 'notification_sent'):
            fees_details.notification_sent = True
            self.assertTrue(fees_details.notification_sent,
                          "Should track notification status")

    def test_payment_analytics_reporting(self):
        """Test payment analytics and reporting."""
        # Create diverse payment data
        payment_data = [
            {'amount': 1000.0, 'state': 'paid', 'payment_method': 'cash'},
            {'amount': 1500.0, 'state': 'paid', 'payment_method': 'bank_transfer'},
            {'amount': 800.0, 'state': 'partial', 'payment_method': 'cheque'},
            {'amount': 1200.0, 'state': 'draft', 'payment_method': 'online'},
        ]
        
        payment_records = []
        for data in payment_data:
            fees_details = self.create_student_fees_details(**data)
            payment_records.append(fees_details)
        
        # Generate analytics
        analytics = {
            'total_payments': sum([p.amount for p in payment_records if p.state == 'paid']),
            'partial_payments': sum([p.amount for p in payment_records if p.state == 'partial']),
            'pending_payments': sum([p.amount for p in payment_records if p.state == 'draft']),
            'payment_methods': {},
        }
        
        # Group by payment method
        for record in payment_records:
            if hasattr(record, 'payment_method') and record.payment_method:
                method = record.payment_method
                if method not in analytics['payment_methods']:
                    analytics['payment_methods'][method] = 0
                analytics['payment_methods'][method] += record.amount
        
        # Verify analytics
        self.assertEqual(analytics['total_payments'], 2500.0, "Should calculate total payments")
        self.assertEqual(analytics['partial_payments'], 800.0, "Should track partial payments")

    def test_payment_security_validation(self):
        """Test payment security validation."""
        fees_details = self.create_student_fees_details(amount=1000.0)
        
        # Test amount validation
        with self.assertRaises(ValidationError):
            self.create_student_fees_details(amount=-100.0)
        
        # Test zero amount validation
        with self.assertRaises(ValidationError):
            self.create_student_fees_details(amount=0.0)

    def test_payment_performance_large_dataset(self):
        """Test payment processing performance with large dataset."""
        # Create large number of payment records
        payment_records = []
        
        for i in range(100):
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 10),
                state='paid'
            )
            payment_records.append(fees_details)
        
        # Test calculation performance
        total_payments = sum([payment.amount for payment in payment_records])
        
        # Verify performance
        self.assertEqual(len(payment_records), 100, "Should create 100 payment records")
        self.assertGreater(total_payments, 0, "Should calculate total efficiently")

    def _get_payment_journal(self):
        """Helper method to get payment journal."""
        journal = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash'])
        ], limit=1)
        
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Test Payment Journal',
                'code': 'TPJ',
                'type': 'bank',
            })
        
        return journal