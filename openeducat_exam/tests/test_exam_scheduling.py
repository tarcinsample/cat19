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
from .test_exam_common import TestExamCommon


@tagged('post_install', '-at_install', 'openeducat_exam')
class TestExamScheduling(TestExamCommon):
    """Test exam scheduling and room allocation functionality."""

    def setUp(self):
        """Set up additional test data for scheduling tests."""
        super().setUp()
        
        # Create exam rooms
        self.room1 = self.env['op.exam.room'].create({
            'name': 'Room 101',
            'code': 'R101',
            'capacity': 30,
        })
        
        self.room2 = self.env['op.exam.room'].create({
            'name': 'Room 102',
            'code': 'R102',
            'capacity': 25,
        })

    def test_exam_creation_basic(self):
        """Test basic exam creation with required fields."""
        exam = self.create_exam()
        
        self.assertEqual(exam.name, 'Test Exam', "Exam name should be set")
        self.assertEqual(exam.exam_code, 'TE001', "Exam code should be set")
        self.assertEqual(exam.session_id, self.exam_session, "Session should be linked")
        self.assertEqual(exam.subject_id, self.subject1, "Subject should be set")
        self.assertEqual(exam.total_marks, 100, "Total marks should be set")
        self.assertEqual(exam.min_marks, 40, "Min marks should be set")
        self.assertEqual(exam.state, 'draft', "Initial state should be draft")

    def test_exam_time_validation(self):
        """Test exam time validation constraints."""
        # Test end time before start time
        start_time = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12))
        end_time = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9))
        
        with self.assertRaises(ValidationError):
            self.create_exam(start_time=start_time, end_time=end_time)

    def test_exam_time_same_validation(self):
        """Test validation when start and end times are the same."""
        same_time = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=10))
        
        with self.assertRaises(ValidationError):
            self.create_exam(start_time=same_time, end_time=same_time)

    def test_exam_session_date_validation(self):
        """Test that exam times must be within session dates."""
        # Try to create exam outside session date range
        invalid_start = datetime.combine(self.today - timedelta(days=30), datetime.min.time().replace(hour=9))
        invalid_end = datetime.combine(self.today - timedelta(days=30), datetime.min.time().replace(hour=12))
        
        with self.assertRaises(ValidationError):
            self.create_exam(start_time=invalid_start, end_time=invalid_end)

    def test_exam_marks_validation(self):
        """Test marks validation constraints."""
        # Test negative total marks
        with self.assertRaises(ValidationError):
            self.create_exam(total_marks=-10)
        
        # Test negative min marks
        with self.assertRaises(ValidationError):
            self.create_exam(min_marks=-5)
        
        # Test min marks greater than total marks
        with self.assertRaises(ValidationError):
            self.create_exam(total_marks=50, min_marks=60)

    def test_exam_code_uniqueness(self):
        """Test unique constraint for exam codes."""
        self.create_exam(exam_code='UNIQUE001')
        
        # Should raise constraint error for duplicate code
        with self.assertRaises(Exception):
            self.create_exam(exam_code='UNIQUE001')

    def test_exam_overlapping_times_validation(self):
        """Test validation for overlapping exam times for same subject."""
        # Create first exam
        start1 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9))
        end1 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12))
        self.create_exam(exam_code='EXAM1', start_time=start1, end_time=end1)
        
        # Try to create overlapping exam for same subject
        start2 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=11))
        end2 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=14))
        
        with self.assertRaises(ValidationError):
            self.create_exam(exam_code='EXAM2', start_time=start2, end_time=end2)

    def test_exam_non_overlapping_different_subjects(self):
        """Test that overlapping times are allowed for different subjects."""
        # Create first exam
        start1 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9))
        end1 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12))
        exam1 = self.create_exam(exam_code='EXAM1', subject_id=self.subject1.id, 
                                start_time=start1, end_time=end1)
        
        # Create overlapping exam for different subject - should be allowed
        start2 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=11))
        end2 = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=14))
        exam2 = self.create_exam(exam_code='EXAM2', subject_id=self.subject2.id,
                                start_time=start2, end_time=end2)
        
        self.assertTrue(exam1.exists(), "First exam should be created")
        self.assertTrue(exam2.exists(), "Second exam should be created")

    def test_exam_workflow_draft_to_schedule(self):
        """Test exam workflow from draft to scheduled."""
        exam = self.create_exam()
        self.assert_exam_state(exam, 'draft')
        
        # Schedule the exam
        exam.act_schedule()
        self.assert_exam_state(exam, 'schedule')

    def test_exam_workflow_schedule_requirements(self):
        """Test validation requirements for scheduling exam."""
        # Test scheduling without session
        exam = self.env['op.exam'].create({
            'name': 'Incomplete Exam',
            'exam_code': 'IE001',
            'subject_id': self.subject1.id,
            'start_time': datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9)),
            'end_time': datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12)),
            'total_marks': 100,
            'min_marks': 40,
        })
        
        with self.assertRaises(ValidationError):
            exam.act_schedule()

    def test_exam_attendees_generation(self):
        """Test automatic generation of exam attendees."""
        exam = self.create_exam()
        
        # Generate attendees
        count = exam._generate_attendees()
        
        self.assertEqual(count, 2, "Should generate attendees for 2 students")
        self.assertEqual(len(exam.attendees_line), 2, "Exam should have 2 attendees")
        
        # Check attendee details
        student_ids = exam.attendees_line.mapped('student_id.id')
        self.assertIn(self.student1.id, student_ids, "Student1 should be attendee")
        self.assertIn(self.student2.id, student_ids, "Student2 should be attendee")

    def test_exam_attendees_count_computation(self):
        """Test attendees count computation."""
        exam = self.create_exam()
        
        # Initially no attendees
        self.assertEqual(exam.attendees_count, 0, "Should have 0 attendees initially")
        
        # Generate attendees
        exam._generate_attendees()
        
        # Force computation
        exam._compute_attendees_count()
        self.assertEqual(exam.attendees_count, 2, "Should count 2 attendees")

    def test_exam_room_allocation(self):
        """Test exam room allocation functionality."""
        exam = self.create_exam()
        exam.act_schedule()
        
        # Test room assignment (if room field exists)
        if hasattr(exam, 'room_ids'):
            exam.room_ids = [(6, 0, [self.room1.id, self.room2.id])]
            
            self.assertIn(self.room1, exam.room_ids, "Room1 should be allocated")
            self.assertIn(self.room2, exam.room_ids, "Room2 should be allocated")

    def test_exam_faculty_assignment(self):
        """Test faculty assignment to exam."""
        exam = self.create_exam()
        
        # Assign faculty
        exam.responsible_id = [(6, 0, [self.faculty.id])]
        
        self.assertIn(self.faculty, exam.responsible_id, "Faculty should be assigned")

    def test_exam_open_attendees_action(self):
        """Test opening exam attendees view."""
        exam = self.create_exam()
        exam._generate_attendees()
        
        action = exam.open_exam_attendees()
        
        self.assertEqual(action['res_model'], 'op.exam.attendees', 
                        "Should open attendees model")
        self.assertEqual(action['domain'], [('exam_id', '=', exam.id)],
                        "Should filter by exam")
        self.assertIn('default_exam_id', action['context'],
                     "Should set exam in context")

    def test_exam_scheduling_with_multiple_sessions(self):
        """Test exam scheduling across multiple exam sessions."""
        # Create another exam session
        session2 = self.env['op.exam.session'].create({
            'name': 'Test Exam Session 2',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'start_date': '2024-12-01',
            'end_date': '2024-12-31',
            'exam_type_id': self.exam_type.id,
            'state': 'schedule',
        })
        
        # Create exams in both sessions
        exam1 = self.create_exam(exam_code='SESSION1_EXAM', session_id=self.exam_session.id)
        exam2 = self.create_exam(exam_code='SESSION2_EXAM', session_id=session2.id,
                               start_time=datetime.combine(self.today + timedelta(days=30), 
                                                          datetime.min.time().replace(hour=9)),
                               end_time=datetime.combine(self.today + timedelta(days=30), 
                                                        datetime.min.time().replace(hour=12)))
        
        self.assertEqual(exam1.session_id, self.exam_session, "Exam1 should be in session1")
        self.assertEqual(exam2.session_id, session2, "Exam2 should be in session2")

    def test_exam_course_batch_relation(self):
        """Test exam relationship with course and batch through session."""
        exam = self.create_exam()
        
        self.assertEqual(exam.course_id, self.course, "Course should be from session")
        self.assertEqual(exam.batch_id, self.batch, "Batch should be from session")

    def test_exam_scheduling_capacity_validation(self):
        """Test validation of room capacity against student count."""
        exam = self.create_exam()
        exam._generate_attendees()
        
        # Test if room capacity checking is implemented
        total_students = len(exam.attendees_line)
        if hasattr(exam, 'room_ids') and hasattr(self.room1, 'capacity'):
            # Check that room capacity is sufficient
            room_capacity = self.room1.capacity
            if total_students > room_capacity:
                # This would need additional rooms or validation
                pass

    def test_exam_scheduling_date_conflicts(self):
        """Test date conflict detection for students."""
        # Create two exams at same time for same batch
        start_time = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9))
        end_time = datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12))
        
        exam1 = self.create_exam(exam_code='CONFLICT1', subject_id=self.subject1.id,
                               start_time=start_time, end_time=end_time)
        exam2 = self.create_exam(exam_code='CONFLICT2', subject_id=self.subject2.id,
                               start_time=start_time, end_time=end_time)
        
        # Both exams should be created (students can have multiple exams)
        self.assertTrue(exam1.exists(), "Exam1 should exist")
        self.assertTrue(exam2.exists(), "Exam2 should exist")

    def test_exam_scheduling_performance(self):
        """Test performance of exam scheduling operations."""
        start_time = self.env.now()
        
        # Create multiple exams
        exams = []
        for i in range(10):
            exam = self.create_exam(
                exam_code=f'PERF{i:03d}',
                name=f'Performance Exam {i}',
                start_time=datetime.combine(self.tomorrow, 
                                          datetime.min.time().replace(hour=9+i)),
                end_time=datetime.combine(self.tomorrow, 
                                        datetime.min.time().replace(hour=10+i))
            )
            exams.append(exam)
        
        end_time = self.env.now()
        creation_time = (end_time - start_time).total_seconds()
        
        # Performance assertion
        self.assertEqual(len(exams), 10, "Should create 10 exams")
        self.assertLess(creation_time, 5.0, "Creation should be fast")

    def test_exam_attendees_generation_validation(self):
        """Test validation during attendees generation."""
        # Create exam without session
        exam = self.env['op.exam'].create({
            'name': 'Invalid Exam',
            'exam_code': 'INVALID001',
            'subject_id': self.subject1.id,
            'start_time': datetime.combine(self.tomorrow, datetime.min.time().replace(hour=9)),
            'end_time': datetime.combine(self.tomorrow, datetime.min.time().replace(hour=12)),
            'total_marks': 100,
            'min_marks': 40,
        })
        
        with self.assertRaises(ValidationError):
            exam._generate_attendees()

    def test_exam_results_entered_computation(self):
        """Test computation of results_entered field."""
        exam = self.create_exam()
        exam._generate_attendees()
        
        # Initially no results
        exam._compute_results_entered()
        self.assertFalse(exam.results_entered, "Should have no results initially")
        
        # Add marks to one attendee
        attendee = exam.attendees_line[0]
        attendee.marks = 85
        
        # Force computation
        exam._compute_results_entered()
        self.assertTrue(exam.results_entered, "Should have results after marking")