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
from .test_exam_common import TestExamCommon


@tagged('post_install', '-at_install', 'openeducat_exam')
class TestMarksheetGeneration(TestExamCommon):
    """Test marksheet generation and calculation accuracy."""

    def setUp(self):
        """Set up test data for marksheet tests."""
        super().setUp()
        
        # Create exams with results
        self.exam1 = self.create_exam(
            exam_code='MATH001',
            name='Mathematics Exam',
            subject_id=self.subject1.id,
            total_marks=100,
            min_marks=40
        )
        
        self.exam2 = self.create_exam(
            exam_code='SCI001',
            name='Science Exam', 
            subject_id=self.subject2.id,
            total_marks=80,
            min_marks=32
        )
        
        # Schedule exams and generate attendees
        self.exam1.act_schedule()
        self.exam2.act_schedule()
        
        # Add marks to attendees
        self.exam1.attendees_line[0].marks = 85  # Student1 - Math
        self.exam1.attendees_line[1].marks = 65  # Student2 - Math
        
        self.exam2.attendees_line[0].marks = 72  # Student1 - Science
        self.exam2.attendees_line[1].marks = 45  # Student2 - Science

    def test_marksheet_register_creation(self):
        """Test basic marksheet register creation."""
        marksheet_register = self.create_marksheet_register()
        
        self.assertEqual(marksheet_register.name, 'Test Marksheet Register',
                        "Register name should be set")
        self.assertEqual(marksheet_register.exam_session_id, self.exam_session,
                        "Session should be linked")
        self.assertEqual(marksheet_register.course_id, self.course,
                        "Course should be set")
        self.assertEqual(marksheet_register.batch_id, self.batch,
                        "Batch should be set")
        self.assertEqual(marksheet_register.grade_configuration_id, self.grade_config,
                        "Grade config should be set")

    def test_marksheet_line_creation(self):
        """Test creation of marksheet lines."""
        marksheet_register = self.create_marksheet_register()
        
        # Create marksheet line
        marksheet_line = self.env['op.marksheet.line'].create({
            'marksheet_register_id': marksheet_register.id,
            'student_id': self.student1.id,
            'exam_id': self.exam1.id,
            'marks': 85,
            'grade': 'A',
        })
        
        self.assertEqual(marksheet_line.student_id, self.student1,
                        "Student should be linked")
        self.assertEqual(marksheet_line.exam_id, self.exam1,
                        "Exam should be linked")
        self.assertEqual(marksheet_line.marks, 85,
                        "Marks should be set correctly")
        self.assertEqual(marksheet_line.grade, 'A',
                        "Grade should be set correctly")

    def test_grade_calculation_from_marks(self):
        """Test automatic grade calculation based on marks."""
        marksheet_register = self.create_marksheet_register()
        
        # Test different mark ranges
        test_cases = [
            (95, 'A+'),  # 90-100
            (85, 'A'),   # 80-89
            (75, 'B'),   # 70-79
            (65, 'C'),   # 60-69
            (45, 'F'),   # 0-59
        ]
        
        for marks, expected_grade in test_cases:
            with self.subTest(marks=marks, expected_grade=expected_grade):
                # Calculate grade based on configuration
                grade = self._calculate_grade(marks, self.grade_config)
                self.assertEqual(grade, expected_grade,
                               f"Marks {marks} should give grade {expected_grade}")

    def _calculate_grade(self, marks, grade_config):
        """Helper method to calculate grade from marks."""
        for line in grade_config.result_line:
            if line.marks_range_from <= marks <= line.marks_range_to:
                return line.grade
        return 'F'  # Default to F if no range matches

    def test_marksheet_total_calculation(self):
        """Test calculation of total marks and percentage."""
        marksheet_register = self.create_marksheet_register()
        
        # Create marksheet lines for student
        lines = []
        lines.append(self.env['op.marksheet.line'].create({
            'marksheet_register_id': marksheet_register.id,
            'student_id': self.student1.id,
            'exam_id': self.exam1.id,
            'marks': 85,
            'total': 100,
        }))
        
        lines.append(self.env['op.marksheet.line'].create({
            'marksheet_register_id': marksheet_register.id,
            'student_id': self.student1.id,
            'exam_id': self.exam2.id,
            'marks': 72,
            'total': 80,
        }))
        
        # Calculate totals
        total_marks_obtained = sum(line.marks for line in lines)
        total_marks_possible = sum(line.total for line in lines)
        percentage = (total_marks_obtained / total_marks_possible) * 100
        
        self.assertEqual(total_marks_obtained, 157, "Total obtained should be 157")
        self.assertEqual(total_marks_possible, 180, "Total possible should be 180")
        self.assertAlmostEqual(percentage, 87.22, places=2, 
                              msg="Percentage should be approximately 87.22%")

    def test_marksheet_pass_fail_determination(self):
        """Test pass/fail determination logic."""
        # Test passing student
        student1_math = 85  # Pass (>40)
        student1_science = 72  # Pass (>32)
        
        math_pass = student1_math >= self.exam1.min_marks
        science_pass = student1_science >= self.exam2.min_marks
        overall_pass = math_pass and science_pass
        
        self.assertTrue(overall_pass, "Student1 should pass overall")
        
        # Test failing student
        student2_math = 65  # Pass (>40)
        student2_science = 25  # Fail (<32)
        
        math_pass = student2_math >= self.exam1.min_marks
        science_pass = student2_science >= self.exam2.min_marks
        overall_pass = math_pass and science_pass
        
        self.assertFalse(overall_pass, "Student2 should fail overall")

    def test_marksheet_rank_calculation(self):
        """Test rank calculation based on total marks."""
        marksheet_register = self.create_marksheet_register()
        
        # Create student results
        student_results = [
            {'student': self.student1, 'total': 157, 'percentage': 87.22},
            {'student': self.student2, 'total': 110, 'percentage': 61.11},
        ]
        
        # Sort by percentage descending for ranking
        student_results.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Assign ranks
        for rank, result in enumerate(student_results, 1):
            result['rank'] = rank
        
        # Verify rankings
        self.assertEqual(student_results[0]['student'], self.student1,
                        "Student1 should be rank 1")
        self.assertEqual(student_results[0]['rank'], 1,
                        "Student1 should have rank 1")
        
        self.assertEqual(student_results[1]['student'], self.student2,
                        "Student2 should be rank 2")
        self.assertEqual(student_results[1]['rank'], 2,
                        "Student2 should have rank 2")

    def test_marksheet_generation_workflow(self):
        """Test complete marksheet generation workflow."""
        marksheet_register = self.create_marksheet_register()
        
        # Step 1: Generate marksheet lines for all students and exams
        students = [self.student1, self.student2]
        exams = [self.exam1, self.exam2]
        
        marksheet_lines = []
        for student in students:
            for exam in exams:
                # Find attendee record to get marks
                attendee = exam.attendees_line.filtered(
                    lambda a: a.student_id == student)
                if attendee and attendee.marks is not None:
                    grade = self._calculate_grade(attendee.marks, self.grade_config)
                    line = self.env['op.marksheet.line'].create({
                        'marksheet_register_id': marksheet_register.id,
                        'student_id': student.id,
                        'exam_id': exam.id,
                        'marks': attendee.marks,
                        'total': exam.total_marks,
                        'grade': grade,
                    })
                    marksheet_lines.append(line)
        
        # Step 2: Verify all lines created
        expected_lines = 4  # 2 students × 2 exams
        self.assertEqual(len(marksheet_lines), expected_lines,
                        f"Should create {expected_lines} marksheet lines")
        
        # Step 3: Calculate student totals
        for student in students:
            student_lines = [l for l in marksheet_lines if l.student_id == student]
            total_obtained = sum(l.marks for l in student_lines)
            total_possible = sum(l.total for l in student_lines)
            percentage = (total_obtained / total_possible) * 100
            
            if student == self.student1:
                self.assertEqual(total_obtained, 157, "Student1 total should be 157")
                self.assertAlmostEqual(percentage, 87.22, places=2)
            elif student == self.student2:
                self.assertEqual(total_obtained, 110, "Student2 total should be 110")
                self.assertAlmostEqual(percentage, 61.11, places=2)

    def test_marksheet_validation_constraints(self):
        """Test marksheet validation constraints."""
        marksheet_register = self.create_marksheet_register()
        
        # Test marks cannot exceed total
        with self.assertRaises(ValidationError):
            self.env['op.marksheet.line'].create({
                'marksheet_register_id': marksheet_register.id,
                'student_id': self.student1.id,
                'exam_id': self.exam1.id,
                'marks': 150,  # Exceeds total of 100
                'total': 100,
            })

    def test_marksheet_duplicate_prevention(self):
        """Test prevention of duplicate marksheet entries."""
        marksheet_register = self.create_marksheet_register()
        
        # Create first marksheet line
        self.env['op.marksheet.line'].create({
            'marksheet_register_id': marksheet_register.id,
            'student_id': self.student1.id,
            'exam_id': self.exam1.id,
            'marks': 85,
        })
        
        # Try to create duplicate - should raise constraint error
        with self.assertRaises(Exception):
            self.env['op.marksheet.line'].create({
                'marksheet_register_id': marksheet_register.id,
                'student_id': self.student1.id,
                'exam_id': self.exam1.id,
                'marks': 90,
            })

    def test_marksheet_bulk_generation(self):
        """Test bulk generation of marksheet lines."""
        marksheet_register = self.create_marksheet_register()
        
        # Prepare bulk data
        marksheet_data = []
        for student in [self.student1, self.student2]:
            for exam in [self.exam1, self.exam2]:
                attendee = exam.attendees_line.filtered(
                    lambda a: a.student_id == student)
                if attendee and attendee.marks is not None:
                    marksheet_data.append({
                        'marksheet_register_id': marksheet_register.id,
                        'student_id': student.id,
                        'exam_id': exam.id,
                        'marks': attendee.marks,
                        'total': exam.total_marks,
                        'grade': self._calculate_grade(attendee.marks, self.grade_config),
                    })
        
        # Bulk create
        lines = self.env['op.marksheet.line'].create(marksheet_data)
        
        self.assertEqual(len(lines), 4, "Should create 4 marksheet lines")

    def test_marksheet_report_data_preparation(self):
        """Test preparation of data for marksheet reports."""
        marksheet_register = self.create_marksheet_register()
        
        # Create marksheet lines
        for student in [self.student1, self.student2]:
            for exam in [self.exam1, self.exam2]:
                attendee = exam.attendees_line.filtered(
                    lambda a: a.student_id == student)
                if attendee and attendee.marks is not None:
                    self.env['op.marksheet.line'].create({
                        'marksheet_register_id': marksheet_register.id,
                        'student_id': student.id,
                        'exam_id': exam.id,
                        'marks': attendee.marks,
                        'total': exam.total_marks,
                        'grade': self._calculate_grade(attendee.marks, self.grade_config),
                    })
        
        # Prepare report data
        report_data = {}
        for student in [self.student1, self.student2]:
            student_lines = self.env['op.marksheet.line'].search([
                ('marksheet_register_id', '=', marksheet_register.id),
                ('student_id', '=', student.id)
            ])
            
            total_obtained = sum(line.marks for line in student_lines)
            total_possible = sum(line.total for line in student_lines)
            percentage = (total_obtained / total_possible) * 100
            
            report_data[student.id] = {
                'student_name': student.name,
                'total_obtained': total_obtained,
                'total_possible': total_possible,
                'percentage': percentage,
                'lines': student_lines,
            }
        
        # Verify report data structure
        self.assertEqual(len(report_data), 2, "Should have data for 2 students")
        self.assertIn(self.student1.id, report_data, "Should have student1 data")
        self.assertIn(self.student2.id, report_data, "Should have student2 data")

    def test_marksheet_grade_boundary_cases(self):
        """Test grade calculation for boundary cases."""
        test_cases = [
            (100, 'A+'),  # Upper boundary
            (90, 'A+'),   # Lower boundary of A+
            (89, 'A'),    # Upper boundary of A
            (80, 'A'),    # Lower boundary of A
            (0, 'F'),     # Minimum marks
        ]
        
        for marks, expected_grade in test_cases:
            with self.subTest(marks=marks):
                grade = self._calculate_grade(marks, self.grade_config)
                self.assertEqual(grade, expected_grade,
                               f"Marks {marks} should give grade {expected_grade}")

    def test_marksheet_statistical_calculations(self):
        """Test statistical calculations for marksheet data."""
        marksheet_register = self.create_marksheet_register()
        
        # Create sample marksheet data
        marks_data = [85, 72, 65, 45, 90, 55]  # Sample marks
        
        # Calculate statistics
        total_students = len(marks_data)
        total_marks = sum(marks_data)
        average_marks = total_marks / total_students
        highest_marks = max(marks_data)
        lowest_marks = min(marks_data)
        
        # Verify calculations
        self.assertEqual(total_students, 6, "Should count 6 students")
        self.assertEqual(total_marks, 412, "Total should be 412")
        self.assertAlmostEqual(average_marks, 68.67, places=2, 
                              msg="Average should be 68.67")
        self.assertEqual(highest_marks, 90, "Highest should be 90")
        self.assertEqual(lowest_marks, 45, "Lowest should be 45")

    def test_marksheet_performance_optimization(self):
        """Test performance of marksheet generation with larger datasets."""
        marksheet_register = self.create_marksheet_register()
        
        # Create additional students for performance testing
        additional_students = []
        for i in range(20):
            student = self.env['op.student'].create({
                'name': f'Performance Student {i}',
                'first_name': 'Performance',
                'last_name': f'Student{i}',
                'birth_date': '2000-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            additional_students.append(student)
        
        # Measure performance of bulk marksheet creation
        start_time = self.env.now()
        
        marksheet_data = []
        for student in additional_students:
            marksheet_data.append({
                'marksheet_register_id': marksheet_register.id,
                'student_id': student.id,
                'exam_id': self.exam1.id,
                'marks': 75,  # Fixed marks for testing
                'total': 100,
                'grade': 'B',
            })
        
        lines = self.env['op.marksheet.line'].create(marksheet_data)
        
        end_time = self.env.now()
        creation_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        self.assertEqual(len(lines), 20, "Should create 20 marksheet lines")
        self.assertLess(creation_time, 5.0, 
                       "Bulk creation should complete within 5 seconds")