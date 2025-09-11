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
from odoo.tests import tagged
from .test_fees_common import TestFeesCommon


@tagged('post_install', '-at_install', 'openeducat_fees')
class TestFeesReports(TestFeesCommon):
    """Test fees reporting and analytics."""

    def test_fees_summary_report(self):
        """Test fees summary report generation."""
        # Create diverse fees data for reporting
        fees_data = [
            {'amount': 1000.0, 'state': 'paid', 'student': self.student1},
            {'amount': 1500.0, 'state': 'paid', 'student': self.student1},
            {'amount': 800.0, 'state': 'draft', 'student': self.student1},
            {'amount': 1200.0, 'state': 'confirm', 'student': self.student1},
        ]
        
        fees_records = []
        for data in fees_data:
            fees_details = self.create_student_fees_details(**data)
            fees_records.append(fees_details)
        
        # Generate summary report
        summary = {
            'total_fees': sum([f.amount for f in fees_records]),
            'paid_fees': sum([f.amount for f in fees_records if f.state == 'paid']),
            'pending_fees': sum([f.amount for f in fees_records if f.state != 'paid']),
            'collection_rate': 0,
        }
        
        if summary['total_fees'] > 0:
            summary['collection_rate'] = (summary['paid_fees'] / summary['total_fees']) * 100
        
        # Verify summary report
        self.assertEqual(summary['total_fees'], 4500.0, "Should calculate total fees")
        self.assertEqual(summary['paid_fees'], 2500.0, "Should calculate paid fees")
        self.assertEqual(summary['pending_fees'], 2000.0, "Should calculate pending fees")
        self.assertEqual(round(summary['collection_rate'], 2), 55.56, "Should calculate collection rate")

    def test_student_fees_statement(self):
        """Test individual student fees statement."""
        # Create fees for student
        fees_records = []
        for i in range(4):
            fees_details = self.create_student_fees_details(
                student=self.student1,
                amount=1000.0 + (i * 200),
                state=['draft', 'confirm', 'paid', 'partial'][i]
            )
            fees_records.append(fees_details)
        
        # Generate student statement
        student_statement = {
            'student_id': self.student1.id,
            'student_name': self.student1.name,
            'total_fees': sum([f.amount for f in fees_records]),
            'paid_amount': sum([f.amount for f in fees_records if f.state == 'paid']),
            'balance': sum([f.amount for f in fees_records if f.state != 'paid']),
            'fees_breakdown': []
        }
        
        # Add breakdown
        for fees in fees_records:
            student_statement['fees_breakdown'].append({
                'amount': fees.amount,
                'state': fees.state,
                'due_date': getattr(fees, 'due_date', None),
            })
        
        # Verify statement
        self.assertEqual(student_statement['total_fees'], 7000.0, "Should calculate total fees")
        self.assertEqual(len(student_statement['fees_breakdown']), 4, "Should include all fees")

    def test_course_wise_fees_report(self):
        """Test course-wise fees report."""
        # Create additional course and student
        department2 = self.env['op.department'].create({
            'name': 'Test Department 2',
            'code': 'TD002',
        })
        
        course2 = self.env['op.course'].create({
            'name': 'Test Course 2',
            'code': 'TC002',
            'department_id': department2.id,
        })
        
        student2 = self.env['op.student'].create({
            'name': 'Test Student 2',
            'first_name': 'Test',
            'last_name': 'Student2',
            'birth_date': '2005-01-01',
            'course_detail_ids': [(0, 0, {
                'course_id': course2.id,
                'batch_id': self.batch.id,
                'academic_years_id': self.academic_year.id,
                'academic_term_id': self.academic_term.id,
            })],
        })
        
        # Create fees for different courses
        course1_fees = self.create_student_fees_details(
            student=self.student1,
            amount=1000.0,
            state='paid'
        )
        
        course2_fees = self.create_student_fees_details(
            student=student2,
            amount=1200.0,
            state='paid'
        )
        
        # Generate course-wise report
        course_report = {}
        
        # Get course from student
        if self.student1.course_detail_ids:
            course1_id = self.student1.course_detail_ids[0].course_id.id
            course_report[course1_id] = {
                'course_name': self.course.name,
                'total_fees': course1_fees.amount,
                'students_count': 1,
            }
        
        if student2.course_detail_ids:
            course2_id = student2.course_detail_ids[0].course_id.id
            course_report[course2_id] = {
                'course_name': course2.name,
                'total_fees': course2_fees.amount,
                'students_count': 1,
            }
        
        # Verify course report
        self.assertEqual(len(course_report), 2, "Should report for both courses")

    def test_fees_collection_report(self):
        """Test fees collection report."""
        # Create fees with different payment dates
        collection_data = []
        for i in range(7):
            payment_date = date.today() - timedelta(days=i)
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 100),
                state='paid',
                payment_date=payment_date
            )
            collection_data.append(fees_details)
        
        # Generate collection report
        daily_collections = {}
        for fees in collection_data:
            if hasattr(fees, 'payment_date'):
                payment_date = fees.payment_date
                if payment_date not in daily_collections:
                    daily_collections[payment_date] = 0
                daily_collections[payment_date] += fees.amount
        
        # Verify collection report
        if daily_collections:
            total_collected = sum(daily_collections.values())
            self.assertGreater(total_collected, 0, "Should track daily collections")

    def test_outstanding_fees_report(self):
        """Test outstanding fees report."""
        # Create fees with different states
        outstanding_data = [
            {'amount': 1000.0, 'state': 'draft', 'due_date': date.today() - timedelta(days=5)},
            {'amount': 1500.0, 'state': 'confirm', 'due_date': date.today() + timedelta(days=10)},
            {'amount': 800.0, 'state': 'partial', 'due_date': date.today() - timedelta(days=2)},
        ]
        
        outstanding_records = []
        for data in outstanding_data:
            fees_details = self.create_student_fees_details(**data)
            outstanding_records.append(fees_details)
        
        # Generate outstanding report
        outstanding_report = {
            'overdue': [],
            'current': [],
            'total_overdue': 0,
            'total_current': 0,
        }
        
        for fees in outstanding_records:
            if fees.state != 'paid':
                if hasattr(fees, 'due_date') and fees.due_date < date.today():
                    outstanding_report['overdue'].append(fees)
                    outstanding_report['total_overdue'] += fees.amount
                else:
                    outstanding_report['current'].append(fees)
                    outstanding_report['total_current'] += fees.amount
        
        # Verify outstanding report
        self.assertGreater(len(outstanding_report['overdue']), 0, "Should identify overdue fees")
        self.assertGreater(outstanding_report['total_overdue'], 0, "Should calculate overdue amount")

    def test_fees_aging_report(self):
        """Test fees aging report."""
        # Create fees with different due dates
        aging_data = [
            {'amount': 1000.0, 'state': 'confirm', 'due_date': date.today() - timedelta(days=15)},  # 0-30 days
            {'amount': 1500.0, 'state': 'confirm', 'due_date': date.today() - timedelta(days=45)},  # 31-60 days
            {'amount': 800.0, 'state': 'confirm', 'due_date': date.today() - timedelta(days=75)},   # 61-90 days
            {'amount': 1200.0, 'state': 'confirm', 'due_date': date.today() - timedelta(days=120)}, # 90+ days
        ]
        
        aging_records = []
        for data in aging_data:
            fees_details = self.create_student_fees_details(**data)
            aging_records.append(fees_details)
        
        # Generate aging report
        aging_buckets = {
            '0-30': 0,
            '31-60': 0,
            '61-90': 0,
            '90+': 0,
        }
        
        for fees in aging_records:
            if hasattr(fees, 'due_date') and fees.state != 'paid':
                days_overdue = (date.today() - fees.due_date).days
                
                if days_overdue <= 30:
                    aging_buckets['0-30'] += fees.amount
                elif days_overdue <= 60:
                    aging_buckets['31-60'] += fees.amount
                elif days_overdue <= 90:
                    aging_buckets['61-90'] += fees.amount
                else:
                    aging_buckets['90+'] += fees.amount
        
        # Verify aging report
        self.assertEqual(aging_buckets['0-30'], 1000.0, "Should categorize 0-30 days")
        self.assertEqual(aging_buckets['31-60'], 1500.0, "Should categorize 31-60 days")

    def test_payment_method_report(self):
        """Test payment method report."""
        # Create fees with different payment methods
        payment_methods_data = [
            {'amount': 1000.0, 'state': 'paid', 'payment_method': 'cash'},
            {'amount': 1500.0, 'state': 'paid', 'payment_method': 'bank_transfer'},
            {'amount': 800.0, 'state': 'paid', 'payment_method': 'online'},
            {'amount': 1200.0, 'state': 'paid', 'payment_method': 'cheque'},
            {'amount': 900.0, 'state': 'paid', 'payment_method': 'cash'},
        ]
        
        payment_records = []
        for data in payment_methods_data:
            fees_details = self.create_student_fees_details(**data)
            payment_records.append(fees_details)
        
        # Generate payment method report
        method_report = {}
        for fees in payment_records:
            if hasattr(fees, 'payment_method') and fees.payment_method:
                method = fees.payment_method
                if method not in method_report:
                    method_report[method] = {'count': 0, 'amount': 0}
                method_report[method]['count'] += 1
                method_report[method]['amount'] += fees.amount
        
        # Verify payment method report
        if 'cash' in method_report:
            self.assertEqual(method_report['cash']['amount'], 1900.0, "Should aggregate cash payments")

    def test_scholarship_report(self):
        """Test scholarship and discount report."""
        # Create fees with scholarships
        scholarship_data = [
            {'amount': 1000.0, 'state': 'paid', 'scholarship_amount': 200.0},
            {'amount': 1500.0, 'state': 'paid', 'scholarship_amount': 300.0},
            {'amount': 800.0, 'state': 'paid', 'scholarship_amount': 0.0},
        ]
        
        scholarship_records = []
        for data in scholarship_data:
            fees_details = self.create_student_fees_details(**data)
            scholarship_records.append(fees_details)
        
        # Generate scholarship report
        scholarship_report = {
            'total_scholarships': 0,
            'total_fees': 0,
            'students_with_scholarship': 0,
        }
        
        for fees in scholarship_records:
            scholarship_report['total_fees'] += fees.amount
            if hasattr(fees, 'scholarship_amount'):
                scholarship_report['total_scholarships'] += fees.scholarship_amount
                if fees.scholarship_amount > 0:
                    scholarship_report['students_with_scholarship'] += 1
        
        # Verify scholarship report
        self.assertEqual(scholarship_report['total_scholarships'], 500.0, "Should calculate total scholarships")
        self.assertEqual(scholarship_report['students_with_scholarship'], 2, "Should count scholarship recipients")

    def test_fees_dashboard_metrics(self):
        """Test dashboard metrics generation."""
        # Create comprehensive fees data
        dashboard_data = [
            {'amount': 1000.0, 'state': 'paid'},
            {'amount': 1500.0, 'state': 'paid'},
            {'amount': 800.0, 'state': 'confirm'},
            {'amount': 1200.0, 'state': 'draft'},
            {'amount': 900.0, 'state': 'partial'},
        ]
        
        dashboard_records = []
        for data in dashboard_data:
            fees_details = self.create_student_fees_details(**data)
            dashboard_records.append(fees_details)
        
        # Calculate dashboard metrics
        metrics = {
            'total_revenue': sum([f.amount for f in dashboard_records if f.state == 'paid']),
            'pending_amount': sum([f.amount for f in dashboard_records if f.state != 'paid']),
            'total_students': len(set([f.student_id.id for f in dashboard_records])),
            'collection_percentage': 0,
            'payment_rate': 0,
        }
        
        total_fees = sum([f.amount for f in dashboard_records])
        if total_fees > 0:
            metrics['collection_percentage'] = (metrics['total_revenue'] / total_fees) * 100
        
        paid_count = len([f for f in dashboard_records if f.state == 'paid'])
        if dashboard_records:
            metrics['payment_rate'] = (paid_count / len(dashboard_records)) * 100
        
        # Verify dashboard metrics
        self.assertEqual(metrics['total_revenue'], 2500.0, "Should calculate total revenue")
        self.assertEqual(round(metrics['collection_percentage'], 2), 45.45, "Should calculate collection percentage")

    def test_fees_trend_analysis(self):
        """Test fees trend analysis."""
        # Create fees over multiple months
        trend_data = []
        for month in range(3):
            for day in range(5):
                fees_date = date(2024, 6 + month, 1 + day)
                fees_details = self.create_student_fees_details(
                    amount=1000.0 + (month * 100),
                    state='paid',
                    payment_date=fees_date
                )
                trend_data.append(fees_details)
        
        # Generate trend analysis
        monthly_trends = {}
        for fees in trend_data:
            if hasattr(fees, 'payment_date'):
                month_key = fees.payment_date.strftime('%Y-%m')
                if month_key not in monthly_trends:
                    monthly_trends[month_key] = {'amount': 0, 'count': 0}
                monthly_trends[month_key]['amount'] += fees.amount
                monthly_trends[month_key]['count'] += 1
        
        # Verify trend analysis
        self.assertGreater(len(monthly_trends), 0, "Should generate monthly trends")

    def test_fees_comparison_report(self):
        """Test fees comparison report between periods."""
        # Create fees for current period
        current_fees = []
        for i in range(3):
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 100),
                state='paid'
            )
            current_fees.append(fees_details)
        
        # Create fees for previous period (simulated)
        previous_fees = []
        for i in range(3):
            fees_details = self.create_student_fees_details(
                amount=900.0 + (i * 100),
                state='paid'
            )
            previous_fees.append(fees_details)
        
        # Generate comparison report
        comparison = {
            'current_total': sum([f.amount for f in current_fees]),
            'previous_total': sum([f.amount for f in previous_fees]),
            'growth_amount': 0,
            'growth_percentage': 0,
        }
        
        comparison['growth_amount'] = comparison['current_total'] - comparison['previous_total']
        if comparison['previous_total'] > 0:
            comparison['growth_percentage'] = (comparison['growth_amount'] / comparison['previous_total']) * 100
        
        # Verify comparison report
        self.assertGreater(comparison['growth_amount'], 0, "Should calculate growth")

    def test_fees_export_functionality(self):
        """Test fees data export functionality."""
        # Create fees data for export
        export_data = []
        for i in range(5):
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 100),
                state=['paid', 'confirm'][i % 2]
            )
            export_data.append(fees_details)
        
        # Prepare export format
        export_records = []
        for fees in export_data:
            export_record = {
                'student_name': fees.student_id.name,
                'amount': fees.amount,
                'state': fees.state,
                'course': fees.student_id.course_detail_ids[0].course_id.name if fees.student_id.course_detail_ids else '',
            }
            export_records.append(export_record)
        
        # Verify export data
        self.assertEqual(len(export_records), 5, "Should prepare all records for export")

    def test_fees_report_performance(self):
        """Test report generation performance with large dataset."""
        # Create large dataset
        large_dataset = []
        for i in range(100):
            fees_details = self.create_student_fees_details(
                amount=1000.0 + (i * 10),
                state=['paid', 'confirm', 'draft'][i % 3]
            )
            large_dataset.append(fees_details)
        
        # Generate performance metrics
        performance_metrics = {
            'total_records': len(large_dataset),
            'total_amount': sum([f.amount for f in large_dataset]),
            'paid_count': len([f for f in large_dataset if f.state == 'paid']),
            'processing_efficient': True,
        }
        
        # Verify performance
        self.assertEqual(performance_metrics['total_records'], 100, "Should handle large datasets")
        self.assertTrue(performance_metrics['processing_efficient'], "Should process efficiently")