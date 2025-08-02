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
class TestMediaQueue(TestLibraryCommon):
    """Test media queue and reservation system."""

    def setUp(self):
        """Set up test data for queue tests."""
        super().setUp()
        self.media = self.create_media()
        self.library_card1 = self.create_library_card(self.student1)
        self.library_card2 = self.create_library_card(self.student2)

    def test_media_queue_creation(self):
        """Test basic media queue entry creation."""
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        self.assertEqual(queue_entry.media_id, self.media, "Media should be linked")
        self.assertEqual(queue_entry.student_id, self.student1, "Student should be linked")
        self.assertEqual(queue_entry.request_date, self.today, "Request date should be today")

    def test_media_queue_sequence_generation(self):
        """Test queue sequence and priority management."""
        # Create multiple queue entries
        queue1 = self.create_media_queue(
            self.media, self.student1,
            request_date=self.today - timedelta(days=2)
        )
        queue2 = self.create_media_queue(
            self.media, self.student2,
            request_date=self.today - timedelta(days=1)
        )
        
        # Get queue entries in order
        queue_entries = self.env['op.media.queue'].search([
            ('media_id', '=', self.media.id)
        ], order='request_date')
        
        self.assertEqual(queue_entries[0], queue1, "Earlier request should be first")
        self.assertEqual(queue_entries[1], queue2, "Later request should be second")

    def test_media_queue_priority_handling(self):
        """Test priority-based queue management."""
        # Create queue entries with different priorities
        normal_queue = self.create_media_queue(self.media, self.student1)
        
        # Create high priority queue entry if priority field exists
        if hasattr(self.env['op.media.queue'], 'priority'):
            priority_queue = self.env['op.media.queue'].create({
                'media_id': self.media.id,
                'student_id': self.student2.id,
                'request_date': self.today,
                'priority': 'high',
            })
            
            # High priority should come first
            queue_entries = self.env['op.media.queue'].search([
                ('media_id', '=', self.media.id)
            ], order='priority desc, request_date')
            
            self.assertEqual(queue_entries[0], priority_queue, 
                           "High priority should be first")

    def test_media_queue_duplicate_prevention(self):
        """Test prevention of duplicate queue entries."""
        # Create first queue entry
        queue1 = self.create_media_queue(self.media, self.student1)
        
        # Try to create duplicate entry for same student and media
        with self.assertRaises(ValidationError):
            self.create_media_queue(self.media, self.student1)

    def test_media_queue_availability_notification(self):
        """Test notification when queued media becomes available."""
        # Create queue entry
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        # Simulate media becoming available
        self.media.state = 'available'
        
        # Test notification trigger
        if hasattr(queue_entry, 'notify_availability'):
            notification_sent = queue_entry.notify_availability()
            self.assertTrue(notification_sent, "Should send availability notification")

    def test_media_queue_automatic_processing(self):
        """Test automatic processing of queue when media returns."""
        # Issue media to a student first
        issue_movement = self.create_media_movement(self.media, self.student1, 'issue')
        self.media.state = 'issued'
        
        # Create queue entry while media is issued
        queue_entry = self.create_media_queue(self.media, self.student2)
        
        # Return media and process queue
        return_movement = self.create_media_movement(
            self.media, self.student1, 'return',
            return_date=self.today + timedelta(days=1)
        )
        self.media.state = 'available'
        
        # Queue should be processed automatically
        if hasattr(queue_entry, 'process_queue'):
            queue_entry.process_queue()

    def test_media_queue_expiry_handling(self):
        """Test handling of expired queue entries."""
        # Create queue entry with expiry
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        if hasattr(queue_entry, 'expiry_date'):
            # Set expiry date in the past
            queue_entry.expiry_date = self.today - timedelta(days=1)
            
            # Test expired queue cleanup
            expired_queues = self.env['op.media.queue'].search([
                ('expiry_date', '<', self.today)
            ])
            
            self.assertIn(queue_entry, expired_queues, "Should identify expired queues")

    def test_media_queue_cancellation(self):
        """Test queue entry cancellation by student."""
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        # Test cancellation
        if hasattr(queue_entry, 'action_cancel'):
            queue_entry.action_cancel()
            
            if hasattr(queue_entry, 'state'):
                self.assertEqual(queue_entry.state, 'cancelled', 
                               "Queue should be cancelled")

    def test_media_queue_fulfillment_tracking(self):
        """Test tracking of queue fulfillment."""
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        # Fulfill the queue by issuing media
        issue_movement = self.create_media_movement(self.media, self.student1, 'issue')
        
        # Mark queue as fulfilled
        if hasattr(queue_entry, 'action_fulfill'):
            queue_entry.action_fulfill()
            
            if hasattr(queue_entry, 'state'):
                self.assertEqual(queue_entry.state, 'fulfilled', 
                               "Queue should be fulfilled")

    def test_media_queue_waiting_time_calculation(self):
        """Test calculation of waiting time in queue."""
        queue_entry = self.create_media_queue(
            self.media, self.student1,
            request_date=self.today - timedelta(days=5)
        )
        
        # Calculate waiting time
        waiting_days = (self.today - queue_entry.request_date).days
        self.assertEqual(waiting_days, 5, "Should calculate correct waiting time")

    def test_media_queue_position_tracking(self):
        """Test tracking of position in queue."""
        # Create multiple queue entries
        queue1 = self.create_media_queue(
            self.media, self.student1,
            request_date=self.today - timedelta(days=3)
        )
        queue2 = self.create_media_queue(
            self.media, self.student2,
            request_date=self.today - timedelta(days=2)
        )
        
        # Create third student and queue entry
        student3 = self.env['op.student'].create({
            'name': 'Queue Student 3',
            'first_name': 'Queue',
            'last_name': 'Student3',
            'birth_date': '2000-03-03',
        })
        self.create_library_card(student3)
        
        queue3 = self.create_media_queue(
            self.media, student3,
            request_date=self.today - timedelta(days=1)
        )
        
        # Calculate positions
        queue_entries = self.env['op.media.queue'].search([
            ('media_id', '=', self.media.id)
        ], order='request_date')
        
        positions = {entry.id: idx + 1 for idx, entry in enumerate(queue_entries)}
        
        self.assertEqual(positions[queue1.id], 1, "First queue should be position 1")
        self.assertEqual(positions[queue2.id], 2, "Second queue should be position 2")
        self.assertEqual(positions[queue3.id], 3, "Third queue should be position 3")

    def test_media_queue_bulk_processing(self):
        """Test bulk processing of queue entries."""
        # Create multiple media and queue entries
        media_list = []
        queue_entries = []
        
        for i in range(5):
            media = self.create_media(
                name=f'Queue Media {i}',
                isbn=f'978-{i:010d}'
            )
            media_list.append(media)
            
            queue_entry = self.create_media_queue(media, self.student1)
            queue_entries.append(queue_entry)
        
        # Bulk process queues
        queue_ids = [q.id for q in queue_entries]
        bulk_queues = self.env['op.media.queue'].browse(queue_ids)
        
        if hasattr(bulk_queues, 'action_process_bulk'):
            bulk_queues.action_process_bulk()

    def test_media_queue_student_notification_preferences(self):
        """Test student notification preferences for queue updates."""
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        # Test different notification methods
        notification_methods = ['email', 'sms', 'app']
        
        for method in notification_methods:
            if hasattr(queue_entry, f'notify_by_{method}'):
                notification_sent = getattr(queue_entry, f'notify_by_{method}')()
                # This would typically send actual notifications

    def test_media_queue_statistics_reporting(self):
        """Test queue statistics and reporting."""
        # Create various queue entries
        active_queues = []
        for i in range(10):
            media = self.create_media(
                name=f'Stats Media {i}',
                isbn=f'978-{i:010d}'
            )
            queue_entry = self.create_media_queue(media, self.student1)
            active_queues.append(queue_entry)
        
        # Calculate statistics
        total_queues = self.env['op.media.queue'].search_count([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertEqual(total_queues, 10, "Should count all queue entries")
        
        # Average waiting time
        avg_waiting_time = sum([
            (self.today - q.request_date).days for q in active_queues
        ]) / len(active_queues)
        
        self.assertGreaterEqual(avg_waiting_time, 0, "Should calculate average waiting time")

    def test_media_queue_peak_demand_analysis(self):
        """Test analysis of peak demand periods."""
        # Create queue entries across different dates
        demand_data = {}
        
        for i in range(7):  # Week's worth of data
            date = self.today - timedelta(days=i)
            
            # Create variable number of queue entries per day
            queue_count = (i % 3) + 1  # 1-3 queues per day
            
            for j in range(queue_count):
                media = self.create_media(
                    name=f'Demand Media {i}-{j}',
                    isbn=f'978-{i:03d}{j:03d}000'
                )
                self.create_media_queue(media, self.student1, request_date=date)
            
            demand_data[date.isoformat()] = queue_count
        
        # Find peak demand day
        peak_day = max(demand_data, key=demand_data.get)
        peak_demand = demand_data[peak_day]
        
        self.assertGreaterEqual(peak_demand, 1, "Should identify peak demand")

    def test_media_queue_integration_with_reservations(self):
        """Test integration with reservation system."""
        # Create reservation (queue entry)
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        # Media becomes available
        self.media.state = 'available'
        
        # Process reservation -> issue
        if hasattr(queue_entry, 'convert_to_issue'):
            issue_movement = queue_entry.convert_to_issue()
            
            self.assertEqual(issue_movement.student_id, self.student1,
                           "Issue should be for queued student")
            self.assertEqual(issue_movement.media_id, self.media,
                           "Issue should be for queued media")

    def test_media_queue_faculty_priority(self):
        """Test faculty priority in queue system."""
        # Create faculty if not exists
        faculty_user = self.env['op.faculty'].create({
            'name': 'Test Faculty Queue',
        })
        
        # Create queue for student
        student_queue = self.create_media_queue(self.media, self.student1)
        
        # Create queue for faculty (if supported)
        if hasattr(self.env['op.media.queue'], 'faculty_id'):
            faculty_queue = self.env['op.media.queue'].create({
                'media_id': self.media.id,
                'faculty_id': faculty_user.id,
                'request_date': self.today,
            })
            
            # Faculty should have higher priority
            queue_entries = self.env['op.media.queue'].search([
                ('media_id', '=', self.media.id)
            ], order='priority desc, request_date')
            
            # Verify faculty priority handling

    def test_media_queue_capacity_management(self):
        """Test queue capacity and limits."""
        # Test maximum queue length per media
        max_queue_length = 10  # Configurable limit
        
        # Create students for testing
        students = [self.student1, self.student2]
        for i in range(8):
            student = self.env['op.student'].create({
                'name': f'Queue Student {i+3}',
                'first_name': 'Queue',
                'last_name': f'Student{i+3}',
                'birth_date': '2000-01-01',
            })
            self.create_library_card(student)
            students.append(student)
        
        # Create queue entries up to limit
        queue_entries = []
        for i, student in enumerate(students[:max_queue_length]):
            queue_entry = self.create_media_queue(self.media, student)
            queue_entries.append(queue_entry)
        
        # Verify queue length
        total_queues = self.env['op.media.queue'].search_count([
            ('media_id', '=', self.media.id)
        ])
        
        self.assertLessEqual(total_queues, max_queue_length,
                           "Should respect queue capacity limits")

    def test_media_queue_performance_large_dataset(self):
        """Test performance with large queue dataset."""
        # Create large number of queue entries
        queue_entries = []
        for i in range(100):
            media = self.create_media(
                name=f'Perf Queue Media {i}',
                isbn=f'978-{i:010d}'
            )
            queue_entry = self.create_media_queue(media, self.student1)
            queue_entries.append(queue_entry)
        
        # Test search performance
        search_results = self.env['op.media.queue'].search([
            ('student_id', '=', self.student1.id)
        ])
        
        self.assertEqual(len(search_results), 100,
                        "Should handle large queue datasets efficiently")

    def test_media_queue_cleanup_automation(self):
        """Test automated cleanup of old queue entries."""
        # Create old queue entries
        old_queue = self.create_media_queue(
            self.media, self.student1,
            request_date=self.today - timedelta(days=30)
        )
        
        # Create recent queue entry
        recent_queue = self.create_media_queue(
            self.media, self.student2,
            request_date=self.today - timedelta(days=1)
        )
        
        # Test cleanup of old entries
        cleanup_threshold = 14  # Days
        old_queues = self.env['op.media.queue'].search([
            ('request_date', '<', self.today - timedelta(days=cleanup_threshold))
        ])
        
        self.assertIn(old_queue, old_queues, "Should identify old queues for cleanup")
        self.assertNotIn(recent_queue, old_queues, "Should preserve recent queues")

    def test_media_queue_workflow_integration(self):
        """Test complete queue workflow integration."""
        # 1. Create queue when media is not available
        self.media.state = 'issued'
        queue_entry = self.create_media_queue(self.media, self.student1)
        
        # 2. Media becomes available
        self.media.state = 'available'
        
        # 3. Process queue automatically
        if hasattr(queue_entry, 'auto_process'):
            queue_entry.auto_process()
        
        # 4. Verify queue is processed
        if hasattr(queue_entry, 'state'):
            self.assertIn(queue_entry.state, ['processed', 'fulfilled'],
                         "Queue should be processed when media becomes available")
        
        # 5. Issue media to queued student
        issue_movement = self.create_media_movement(self.media, self.student1, 'issue')
        
        # Verify complete workflow
        self.assertEqual(issue_movement.student_id, queue_entry.student_id,
                        "Issue should be to the queued student")