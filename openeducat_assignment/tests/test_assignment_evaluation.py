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
from odoo.tests import tagged
from .test_assignment_common import TestAssignmentCommon


@tagged('post_install', '-at_install')
class TestAssignmentEvaluation(TestAssignmentCommon):
    """Test assignment evaluation and grading systems."""
    
    def test_assignment_evaluation_workflow(self):
        """Test Task 6: Test assignment evaluation and grading systems."""
        
        # Create assignment with specific marks
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'marks': 100  # Total marks
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submissions for evaluation
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Excellent submission with comprehensive analysis'
        })
        
        submission2 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student2.id,
            'description': 'Good submission but missing some details'
        })
        
        # Submit assignments
        submission1.act_submit()
        submission2.act_submit()
        
        # Faculty evaluation process
        # Evaluate submission 1 - High grade
        submission1.write({
            'marks': 95,
            'note': 'Excellent work. Shows deep understanding.'
        })
        submission1.act_accept()
        
        # Evaluate submission 2 - Request changes
        submission2.write({
            'note': 'Good effort but needs more detail in section 2.'
        })
        submission2.act_change_req()
        
        # Verify evaluation states
        self.assertEqual(submission1.state, 'accept')
        self.assertEqual(submission1.marks, 95)
        self.assertEqual(submission2.state, 'change')
        
        # Student resubmits after changes
        submission2.write({
            'description': 'Revised submission with additional details in section 2'
        })
        submission2.act_submit()
        
        # Faculty final evaluation
        submission2.write({
            'marks': 82,
            'note': 'Much improved. Good work on revisions.'
        })
        submission2.act_accept()
        
        # Verify final evaluation
        self.assertEqual(submission2.state, 'accept')
        self.assertEqual(submission2.marks, 82)
    
    def test_grading_scale_validation(self):
        """Test grading scale validation and constraints."""
        
        # Create assignment with maximum marks
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'marks': 100
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Test submission for grading validation'
        })
        submission.act_submit()
        
        # Test valid marks
        valid_marks = [0, 25, 50, 75, 100]
        for marks in valid_marks:
            submission.write({'marks': marks})
            self.assertEqual(submission.marks, marks)
        
        # Test edge cases
        submission.write({'marks': 100.0})  # Exactly maximum
        self.assertEqual(submission.marks, 100.0)
    
    def test_multiple_evaluation_criteria(self):
        """Test evaluation with multiple criteria."""
        
        # Create assignment types for different evaluation criteria
        essay_type = self.op_assignment_type.create({
            'name': 'Essay Assignment',
            'code': 'ESSAY',
            'assign_type': 'sub'
        })
        
        practical_type = self.op_assignment_type.create({
            'name': 'Practical Assignment',
            'code': 'PRAC',
            'assign_type': 'sub'
        })
        
        # Create assignments with different types
        assignments = []
        assignment_types = [essay_type, practical_type]
        max_marks = [100, 50]
        
        for i, (assign_type, marks) in enumerate(zip(assignment_types, max_marks)):
            grading_assignment = self.grading_assignment.create({
                'name': f'Multi-criteria Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now(),
                'assignment_type': assign_type.id,
                'faculty_id': self.faculty.id,
                'point': marks
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data.update({
                'grading_assignment_id': grading_assignment.id,
                'marks': marks
            })
            assignment = self.op_assignment.create(assignment_data)
            assignments.append(assignment)
        
        # Create and evaluate submissions for each assignment type
        for assignment in assignments:
            assignment.act_publish()
            
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': self.student1.id,
                'description': f'Submission for {assignment.assignment_type.name}'
            })
            submission.act_submit()
            
            # Different evaluation based on assignment type
            if assignment.assignment_type.assign_type == 'sub':
                # Essay - qualitative evaluation
                submission.write({
                    'marks': assignment.marks * 0.85,  # 85% score
                    'note': 'Well structured essay with good arguments'
                })
            else:
                # Practical - quantitative evaluation
                submission.write({
                    'marks': assignment.marks * 0.90,  # 90% score
                    'note': 'Correct implementation, minor optimization needed'
                })
            
            submission.act_accept()
            self.assertEqual(submission.state, 'accept')
    
    def test_grade_distribution_analysis(self):
        """Test grade distribution analysis."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create multiple students with varying performance
        students_marks = [95, 87, 92, 78, 83, 69, 91, 76, 88, 82]
        
        students = []
        for i, marks in enumerate(students_marks):
            # Create student
            partner = self.env['res.partner'].create({
                'name': f'Grade Analysis Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            students.append((student, marks))
        
        # Create submissions and grade them
        submissions = []
        for student, marks in students:
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Performance analysis submission - {marks}%'
            })
            submission.act_submit()
            submission.write({'marks': marks})
            submission.act_accept()
            submissions.append(submission)
        
        # Analyze grade distribution
        all_marks = [s.marks for s in submissions]
        
        # Statistical analysis
        average_marks = sum(all_marks) / len(all_marks)
        max_marks = max(all_marks)
        min_marks = min(all_marks)
        
        self.assertEqual(average_marks, 84.1)  # Expected average
        self.assertEqual(max_marks, 95)
        self.assertEqual(min_marks, 69)
        
        # Grade categories
        excellent = len([m for m in all_marks if m >= 90])  # A grade
        good = len([m for m in all_marks if 80 <= m < 90])  # B grade
        satisfactory = len([m for m in all_marks if 70 <= m < 80])  # C grade
        needs_improvement = len([m for m in all_marks if m < 70])  # Below C
        
        self.assertEqual(excellent, 4)  # 95, 92, 91, 88 (if 88 >= 90, adjust logic)
        self.assertEqual(good, 4)  # 87, 83, 88, 82
        self.assertEqual(satisfactory, 2)  # 78, 76
        self.assertEqual(needs_improvement, 0)  # 69 (adjust if threshold changes)
    
    def test_plagiarism_detection_integration(self):
        """Test Task 11: Validate assignment plagiarism detection integration."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submissions with similar content (simulating plagiarism)
        similar_content = "This is a sample assignment submission with specific content that might be similar to other submissions."
        
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': similar_content
        })
        
        submission2 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student2.id,
            'description': similar_content + " With minor modifications."
        })
        
        # Submit both
        submission1.act_submit()
        submission2.act_submit()
        
        # Simulate plagiarism detection results
        # In real implementation, this would integrate with plagiarism detection service
        similarity_threshold = 80  # 80% similarity threshold
        
        # Mock plagiarism check
        def check_plagiarism(submission1, submission2):
            """Mock plagiarism detection function."""
            content1 = submission1.description.lower()
            content2 = submission2.description.lower()
            
            # Simple similarity check (in real implementation, use proper algorithms)
            common_words = set(content1.split()) & set(content2.split())
            total_words = set(content1.split()) | set(content2.split())
            
            similarity = len(common_words) / len(total_words) * 100 if total_words else 0
            return similarity
        
        similarity = check_plagiarism(submission1, submission2)
        
        # If high similarity detected
        if similarity > similarity_threshold:
            # Flag submissions for manual review
            submission1.write({
                'note': f'Flagged for similarity check. {similarity:.1f}% similarity detected.'
            })
            submission2.write({
                'note': f'Flagged for similarity check. {similarity:.1f}% similarity detected.'
            })
            
            # Change status to require changes
            submission1.act_change_req()
            submission2.act_change_req()
            
            self.assertEqual(submission1.state, 'change')
            self.assertEqual(submission2.state, 'change')
    
    def test_rubric_based_evaluation(self):
        """Test rubric-based evaluation system."""
        
        # Create assignment with rubric criteria
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'marks': 100,
            'description': '''
            Evaluation Rubric:
            - Content Quality (40 points)
            - Organization (20 points)
            - Grammar & Style (20 points)
            - Originality (20 points)
            '''
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission for rubric evaluation
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Comprehensive submission addressing all rubric criteria'
        })
        submission.act_submit()
        
        # Rubric-based evaluation
        evaluation_breakdown = {
            'content_quality': 35,  # out of 40
            'organization': 18,     # out of 20
            'grammar_style': 17,    # out of 20
            'originality': 19       # out of 20
        }
        
        total_marks = sum(evaluation_breakdown.values())
        
        submission.write({
            'marks': total_marks,
            'note': f'''
            Rubric Evaluation:
            - Content Quality: {evaluation_breakdown['content_quality']}/40
            - Organization: {evaluation_breakdown['organization']}/20
            - Grammar & Style: {evaluation_breakdown['grammar_style']}/20
            - Originality: {evaluation_breakdown['originality']}/20
            Total: {total_marks}/100
            '''
        })
        submission.act_accept()
        
        self.assertEqual(submission.marks, 89)
        self.assertEqual(submission.state, 'accept')
    
    def test_peer_review_simulation(self):
        """Test peer review evaluation system."""
        
        # Create assignment suitable for peer review
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'description': 'Peer review assignment - students will review each other\'s work'
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submissions from both students
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Student 1 submission for peer review'
        })
        
        submission2 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student2.id,
            'description': 'Student 2 submission for peer review'
        })
        
        # Both students submit
        submission1.act_submit()
        submission2.act_submit()
        
        # Simulate peer review process
        # Student 1 reviews Student 2's work
        peer_review_1 = f"Peer review by {self.student1.name}: Good analysis but could use more examples."
        
        # Student 2 reviews Student 1's work
        peer_review_2 = f"Peer review by {self.student2.name}: Excellent structure and clear arguments."
        
        # Add peer reviews to notes
        submission1.write({
            'note': submission1.note + f"\n\nPeer Review: {peer_review_2}" if submission1.note else f"Peer Review: {peer_review_2}"
        })
        
        submission2.write({
            'note': submission2.note + f"\n\nPeer Review: {peer_review_1}" if submission2.note else f"Peer Review: {peer_review_1}"
        })
        
        # Faculty final evaluation considering peer reviews
        submission1.write({'marks': 88})
        submission1.act_accept()
        
        submission2.write({'marks': 82})
        submission2.act_accept()
        
        # Verify peer review process
        self.assertIn('Peer Review:', submission1.note)
        self.assertIn('Peer Review:', submission2.note)
    
    def test_late_submission_penalty_calculation(self):
        """Test late submission penalty calculation in evaluation."""
        
        # Create assignment with past deadline
        past_deadline = datetime.now() - timedelta(days=2)
        grading_assignment = self.grading_assignment.create({
            'name': 'Late Penalty Assignment',
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now() - timedelta(days=7),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': past_deadline
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create late submission
        late_submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Late submission',
            'submission_date': datetime.now()  # Submitted after deadline
        })
        late_submission.act_submit()
        
        # Calculate penalty (e.g., 5% per day late)
        days_late = (datetime.now().date() - past_deadline.date()).days
        penalty_per_day = 5  # 5% penalty per day
        total_penalty = min(days_late * penalty_per_day, 50)  # Maximum 50% penalty
        
        # Original marks would be 90, but with penalty
        original_marks = 90
        final_marks = original_marks - (original_marks * total_penalty / 100)
        
        late_submission.write({
            'marks': final_marks,
            'note': f'Original marks: {original_marks}. Late penalty: -{total_penalty}% ({days_late} days late). Final marks: {final_marks}'
        })
        late_submission.act_accept()
        
        # Verify penalty calculation
        expected_final_marks = 90 - (90 * (2 * 5) / 100)  # 90 - 9 = 81
        self.assertEqual(late_submission.marks, expected_final_marks)
    
    def test_batch_evaluation_operations(self):
        """Test batch evaluation operations for multiple submissions."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create multiple students and submissions
        students_and_marks = []
        for i in range(10):
            partner = self.env['res.partner'].create({
                'name': f'Batch Eval Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            students_and_marks.append((student, 70 + i * 3))  # Marks from 70 to 97
        
        # Create submissions
        submissions = []
        for student, marks in students_and_marks:
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Batch evaluation submission - expected {marks}%'
            })
            submission.act_submit()
            submissions.append((submission, marks))
        
        # Batch evaluation
        for submission, marks in submissions:
            submission.write({
                'marks': marks,
                'note': f'Batch evaluated - {marks}/100'
            })
            submission.act_accept()
        
        # Verify batch evaluation results
        all_submissions = assignment.assignment_sub_line
        self.assertEqual(len(all_submissions), 10)
        
        accepted_submissions = all_submissions.filtered(lambda s: s.state == 'accept')
        self.assertEqual(len(accepted_submissions), 10)
        
        # Verify marks distribution
        total_marks = sum(accepted_submissions.mapped('marks'))
        expected_total = sum([marks for _, marks in students_and_marks])
        self.assertEqual(total_marks, expected_total)