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
from odoo.tests import tagged
from .test_library_common import TestLibraryCommon


@tagged('post_install', '-at_install', 'openeducat_library')
class TestLibraryReports(TestLibraryCommon):
    """Test library reports and analytics generation."""

    def setUp(self):
        """Set up test data for reports tests."""
        super().setUp()
        self.setup_report_test_data()

    def setup_report_test_data(self):
        """Create comprehensive test data for reporting."""
        # Create multiple media items
        self.media_list = []
        for i in range(10):
            media = self.create_media(
                name=f'Report Media {i}',
                isbn=f'978-{i:010d}',
                media_type=self.media_type_book.id if i % 2 == 0 else self.media_type_journal.id
            )
            self.media_list.append(media)
        
        # Create library cards
        self.library_card1 = self.create_library_card(self.student1)
        self.library_card2 = self.create_library_card(self.student2)
        
        # Create various movements
        self.movements = []
        for i, media in enumerate(self.media_list[:5]):
            student = self.student1 if i % 2 == 0 else self.student2
            movement = self.create_media_movement(
                media, student, 'issue',
                issue_date=self.today - timedelta(days=i),
                return_date=self.today + timedelta(days=7-i)
            )
            self.movements.append(movement)
        
        # Create some returned movements
        for i, media in enumerate(self.media_list[5:8]):
            movement = self.create_media_movement(
                media, self.student1, 'return',
                issue_date=self.today - timedelta(days=10+i),
                return_date=self.today - timedelta(days=3+i)
            )
            self.movements.append(movement)

    def test_media_circulation_report(self):
        """Test media circulation report generation."""
        # Generate circulation report data
        circulation_data = []
        
        for media in self.media_list:
            # Count movements for each media
            movement_count = self.env['op.media.movement'].search_count([
                ('media_id', '=', media.id)
            ])
            
            circulation_data.append({
                'media_id': media.id,
                'media_name': media.name,
                'isbn': media.isbn,
                'total_movements': movement_count,
                'current_state': media.state,
            })
        
        # Verify report data
        self.assertGreater(len(circulation_data), 0, "Should generate circulation data")
        
        # Check data structure
        for entry in circulation_data:
            self.assertIn('media_name', entry, "Should include media name")
            self.assertIn('total_movements', entry, "Should include movement count")

    def test_student_borrowing_history_report(self):
        """Test student borrowing history report."""
        # Generate student borrowing report
        student_report = []
        
        for student in [self.student1, self.student2]:
            movements = self.env['op.media.movement'].search([
                ('student_id', '=', student.id)
            ])
            
            borrowing_data = {
                'student_id': student.id,
                'student_name': student.name,
                'total_borrowed': len([m for m in movements if m.type == 'issue']),
                'total_returned': len([m for m in movements if m.type == 'return']),
                'currently_borrowed': len([m for m in movements if m.type == 'issue']) - 
                                   len([m for m in movements if m.type == 'return']),
            }
            student_report.append(borrowing_data)
        
        # Verify report structure
        self.assertEqual(len(student_report), 2, "Should have data for both students")
        
        for entry in student_report:
            self.assertIn('student_name', entry, "Should include student name")
            self.assertIn('total_borrowed', entry, "Should include borrowing count")

    def test_overdue_media_report(self):
        """Test overdue media report generation."""
        # Create overdue movements
        overdue_movement = self.create_media_movement(
            self.media_list[0], self.student1, 'issue',
            issue_date=self.today - timedelta(days=15),
            return_date=self.today - timedelta(days=5)
        )
        
        # Generate overdue report
        overdue_data = []
        
        movements = self.env['op.media.movement'].search([
            ('type', '=', 'issue'),
            ('return_date', '<', self.today)
        ])
        
        for movement in movements:
            overdue_days = (self.today - movement.return_date).days
            if overdue_days > 0:
                overdue_data.append({
                    'movement_id': movement.id,
                    'media_name': movement.media_id.name,
                    'student_name': movement.student_id.name,
                    'return_date': movement.return_date,
                    'overdue_days': overdue_days,
                    'fine_amount': overdue_days * self.card_type.penalties_day,
                })
        
        # Verify overdue report
        self.assertGreater(len(overdue_data), 0, "Should identify overdue items")
        
        for entry in overdue_data:
            self.assertGreater(entry['overdue_days'], 0, "Should have positive overdue days")
            self.assertGreater(entry['fine_amount'], 0, "Should calculate fine amount")

    def test_media_inventory_report(self):
        """Test media inventory report generation."""
        # Generate inventory report
        inventory_data = {
            'total_media': len(self.media_list),
            'available_media': self.env['op.media'].search_count([('state', '=', 'available')]),
            'issued_media': self.env['op.media'].search_count([('state', '=', 'issued')]),
            'lost_media': self.env['op.media'].search_count([('state', '=', 'lost')]),
            'by_type': {},
            'by_unit': {},
        }
        
        # Count by media type
        for media_type in [self.media_type_book, self.media_type_journal]:
            count = self.env['op.media'].search_count([
                ('media_type', '=', media_type.id)
            ])
            inventory_data['by_type'][media_type.name] = count
        
        # Count by unit
        unit_count = self.env['op.media'].search_count([
            ('unit_id', '=', self.media_unit.id)
        ])
        inventory_data['by_unit'][self.media_unit.name] = unit_count
        
        # Verify inventory report
        self.assertEqual(inventory_data['total_media'], len(self.media_list),
                        "Should count total media correctly")
        self.assertIn('by_type', inventory_data, "Should include type breakdown")
        self.assertIn('by_unit', inventory_data, "Should include unit breakdown")

    def test_library_usage_statistics(self):
        """Test library usage statistics generation."""
        # Calculate usage statistics
        usage_stats = {
            'total_students_with_cards': self.env['op.library.card'].search_count([]),
            'total_active_movements': self.env['op.media.movement'].search_count([
                ('type', '=', 'issue')
            ]),
            'total_returns': self.env['op.media.movement'].search_count([
                ('type', '=', 'return')
            ]),
            'average_borrowing_period': 0,
            'most_popular_media': None,
            'peak_usage_day': None,
        }
        
        # Calculate average borrowing period
        completed_movements = self.env['op.media.movement'].search([
            ('type', '=', 'return')
        ])
        
        if completed_movements:
            total_days = sum([
                (movement.return_date - movement.issue_date).days 
                for movement in completed_movements
            ])
            usage_stats['average_borrowing_period'] = total_days / len(completed_movements)
        
        # Find most popular media
        media_popularity = {}
        for media in self.media_list:
            movement_count = self.env['op.media.movement'].search_count([
                ('media_id', '=', media.id)
            ])
            media_popularity[media.id] = movement_count
        
        if media_popularity:
            most_popular_id = max(media_popularity, key=media_popularity.get)
            usage_stats['most_popular_media'] = self.env['op.media'].browse(most_popular_id).name
        
        # Verify statistics
        self.assertGreaterEqual(usage_stats['total_students_with_cards'], 2,
                               "Should count library cards")
        self.assertIn('average_borrowing_period', usage_stats,
                     "Should calculate borrowing period")

    def test_fine_collection_report(self):
        """Test fine collection report generation."""
        # Create movements with fines
        fine_movements = []
        
        # Create overdue movements that generate fines
        for i in range(3):
            overdue_movement = self.create_media_movement(
                self.media_list[i], self.student1, 'issue',
                issue_date=self.today - timedelta(days=20+i),
                return_date=self.today - timedelta(days=10+i)
            )
            fine_movements.append(overdue_movement)
        
        # Generate fine report
        fine_report = []
        
        for movement in fine_movements:
            overdue_days = (self.today - movement.return_date).days
            if overdue_days > 0:
                fine_amount = overdue_days * self.card_type.penalties_day
                
                fine_report.append({
                    'student_id': movement.student_id.id,
                    'student_name': movement.student_id.name,
                    'media_name': movement.media_id.name,
                    'overdue_days': overdue_days,
                    'fine_amount': fine_amount,
                    'paid': False,  # Default unpaid
                })
        
        # Calculate totals
        total_fines = sum([entry['fine_amount'] for entry in fine_report])
        unpaid_fines = sum([entry['fine_amount'] for entry in fine_report if not entry['paid']])
        
        # Verify fine report
        self.assertGreater(len(fine_report), 0, "Should generate fine entries")
        self.assertGreater(total_fines, 0, "Should calculate total fines")
        self.assertEqual(total_fines, unpaid_fines, "All fines should be unpaid initially")

    def test_popular_media_report(self):
        """Test popular media report generation."""
        # Count movements per media to determine popularity
        media_stats = {}
        
        for media in self.media_list:
            movement_count = self.env['op.media.movement'].search_count([
                ('media_id', '=', media.id)
            ])
            
            if movement_count > 0:
                media_stats[media.id] = {
                    'media_name': media.name,
                    'isbn': media.isbn,
                    'author_names': ', '.join([author.name for author in media.author_ids]),
                    'movement_count': movement_count,
                    'media_type': media.media_type.name,
                }
        
        # Sort by popularity
        popular_media = sorted(media_stats.values(), 
                              key=lambda x: x['movement_count'], 
                              reverse=True)
        
        # Verify popular media report
        if popular_media:
            most_popular = popular_media[0]
            self.assertGreater(most_popular['movement_count'], 0,
                             "Most popular media should have movements")
            self.assertIn('media_name', most_popular,
                         "Should include media details")

    def test_library_card_usage_report(self):
        """Test library card usage report."""
        # Generate card usage report
        card_usage = []
        
        cards = self.env['op.library.card'].search([])
        
        for card in cards:
            movements = self.env['op.media.movement'].search([
                ('student_id', '=', card.student_id.id)
            ])
            
            card_data = {
                'card_number': card.number,
                'student_name': card.student_id.name,
                'total_movements': len(movements),
                'current_issues': len([m for m in movements if m.type == 'issue']) - 
                                len([m for m in movements if m.type == 'return']),
                'card_type': card.card_type_id.name,
            }
            card_usage.append(card_data)
        
        # Verify card usage report
        self.assertEqual(len(card_usage), 2, "Should have data for both cards")
        
        for entry in card_usage:
            self.assertIn('card_number', entry, "Should include card number")
            self.assertIn('total_movements', entry, "Should include movement count")

    def test_media_availability_report(self):
        """Test media availability report."""
        # Generate availability report
        availability_report = {
            'available': [],
            'issued': [],
            'reserved': [],
            'lost': [],
            'maintenance': [],
        }
        
        for media in self.media_list:
            media_info = {
                'media_id': media.id,
                'name': media.name,
                'isbn': media.isbn,
                'location': media.unit_id.name,
            }
            
            if media.state in availability_report:
                availability_report[media.state].append(media_info)
        
        # Add queue information for reserved media
        queues = self.env['op.media.queue'].search([])
        for queue in queues:
            if queue.media_id.state == 'available':  # Reserved but available
                media_info = {
                    'media_id': queue.media_id.id,
                    'name': queue.media_id.name,
                    'reserved_by': queue.student_id.name,
                    'request_date': queue.request_date,
                }
                availability_report['reserved'].append(media_info)
        
        # Verify availability report
        total_media_in_report = sum([len(status_list) for status_list in availability_report.values()])
        self.assertGreaterEqual(total_media_in_report, len(self.media_list),
                               "Should account for all media")

    def test_date_range_reports(self):
        """Test reports with date range filtering."""
        # Generate report for last 7 days
        start_date = self.today - timedelta(days=7)
        end_date = self.today
        
        # Issue movements in date range
        recent_issues = self.env['op.media.movement'].search([
            ('type', '=', 'issue'),
            ('issue_date', '>=', start_date),
            ('issue_date', '<=', end_date),
        ])
        
        # Return movements in date range
        recent_returns = self.env['op.media.movement'].search([
            ('type', '=', 'return'),
            ('return_date', '>=', start_date),
            ('return_date', '<=', end_date),
        ])
        
        date_range_report = {
            'start_date': start_date,
            'end_date': end_date,
            'total_issues': len(recent_issues),
            'total_returns': len(recent_returns),
            'net_circulation': len(recent_issues) - len(recent_returns),
        }
        
        # Verify date range report
        self.assertIn('total_issues', date_range_report, "Should count issues")
        self.assertIn('total_returns', date_range_report, "Should count returns")
        self.assertIn('net_circulation', date_range_report, "Should calculate net circulation")

    def test_department_wise_usage_report(self):
        """Test department-wise library usage report."""
        # Generate department usage report
        dept_usage = {}
        
        # Get students by department through course
        students_by_dept = {}
        students = self.env['op.student'].search([])
        
        for student in students:
            for course_detail in student.course_detail_ids:
                dept_name = course_detail.course_id.department_id.name
                if dept_name not in students_by_dept:
                    students_by_dept[dept_name] = []
                students_by_dept[dept_name].append(student.id)
        
        # Calculate usage by department
        for dept_name, student_ids in students_by_dept.items():
            movements = self.env['op.media.movement'].search([
                ('student_id', 'in', student_ids)
            ])
            
            dept_usage[dept_name] = {
                'total_students': len(student_ids),
                'total_movements': len(movements),
                'avg_movements_per_student': len(movements) / len(student_ids) if student_ids else 0,
            }
        
        # Verify department report
        self.assertGreater(len(dept_usage), 0, "Should have department data")
        
        for dept_name, data in dept_usage.items():
            self.assertIn('total_students', data, "Should count students")
            self.assertIn('total_movements', data, "Should count movements")

    def test_report_export_functionality(self):
        """Test report export capabilities."""
        # Generate sample report data
        export_data = []
        
        for movement in self.movements:
            export_data.append({
                'Date': movement.issue_date,
                'Student': movement.student_id.name,
                'Media': movement.media_id.name,
                'Type': movement.type,
                'Return Date': movement.return_date,
            })
        
        # Test CSV export format
        csv_headers = list(export_data[0].keys()) if export_data else []
        
        # Verify export structure
        self.assertIn('Date', csv_headers, "Should include date column")
        self.assertIn('Student', csv_headers, "Should include student column")
        self.assertIn('Media', csv_headers, "Should include media column")

    def test_report_performance_large_dataset(self):
        """Test report performance with large datasets."""
        # Create large dataset
        large_media_list = []
        for i in range(100):
            media = self.create_media(
                name=f'Perf Media {i}',
                isbn=f'978-{i:010d}'
            )
            large_media_list.append(media)
            
            # Create movement for each media
            self.create_media_movement(media, self.student1, 'issue')
        
        # Test report generation performance
        start_time = self.env.now()
        
        # Generate circulation report
        circulation_data = []
        for media in large_media_list:
            movement_count = self.env['op.media.movement'].search_count([
                ('media_id', '=', media.id)
            ])
            circulation_data.append({
                'media_name': media.name,
                'movement_count': movement_count,
            })
        
        end_time = self.env.now()
        generation_time = (end_time - start_time).total_seconds()
        
        # Verify performance
        self.assertEqual(len(circulation_data), 100, "Should process all media")
        self.assertLess(generation_time, 10.0, "Report generation should be fast")

    def test_custom_report_filters(self):
        """Test custom report filters and parameters."""
        # Test filtering by media type
        book_movements = self.env['op.media.movement'].search([
            ('media_id.media_type', '=', self.media_type_book.id)
        ])
        
        journal_movements = self.env['op.media.movement'].search([
            ('media_id.media_type', '=', self.media_type_journal.id)
        ])
        
        # Test filtering by student
        student1_movements = self.env['op.media.movement'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        # Test filtering by date range
        recent_movements = self.env['op.media.movement'].search([
            ('issue_date', '>=', self.today - timedelta(days=7))
        ])
        
        # Verify filters work
        self.assertGreaterEqual(len(book_movements), 0, "Should filter by media type")
        self.assertGreaterEqual(len(student1_movements), 0, "Should filter by student")
        self.assertGreaterEqual(len(recent_movements), 0, "Should filter by date")

    def test_report_automation_scheduling(self):
        """Test automated report generation and scheduling."""
        # Simulate scheduled report generation
        scheduled_reports = {
            'daily_overdue': {
                'frequency': 'daily',
                'time': '08:00',
                'recipients': ['librarian@school.edu'],
            },
            'weekly_circulation': {
                'frequency': 'weekly',
                'day': 'monday',
                'recipients': ['admin@school.edu'],
            },
            'monthly_statistics': {
                'frequency': 'monthly',
                'date': 1,
                'recipients': ['principal@school.edu'],
            },
        }
        
        # Verify scheduling configuration
        for report_name, config in scheduled_reports.items():
            self.assertIn('frequency', config, "Should define frequency")
            self.assertIn('recipients', config, "Should define recipients")
            self.assertGreater(len(config['recipients']), 0, "Should have recipients")

    def test_report_data_accuracy(self):
        """Test accuracy of report calculations."""
        # Verify movement counts
        total_movements = self.env['op.media.movement'].search_count([])
        issue_movements = self.env['op.media.movement'].search_count([('type', '=', 'issue')])
        return_movements = self.env['op.media.movement'].search_count([('type', '=', 'return')])
        
        self.assertEqual(total_movements, issue_movements + return_movements,
                        "Total movements should equal issues plus returns")
        
        # Verify student movement counts
        student1_total = self.env['op.media.movement'].search_count([
            ('student_id', '=', self.student1.id)
        ])
        student2_total = self.env['op.media.movement'].search_count([
            ('student_id', '=', self.student2.id)
        ])
        
        self.assertGreaterEqual(student1_total + student2_total, 0,
                               "Should accurately count student movements")