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
class TestAssignmentReporting(TestAssignmentCommon):
    """Test assignment reporting and analytics functionality."""
    
    def test_assignment_analytics_dashboard(self):
        """Test Task 8: Test assignment reporting and analytics functionality."""
        
        # Create multiple assignments for comprehensive analytics
        assignments = []
        for i in range(5):
            grading_assignment = self.grading_assignment.create({
                'name': f'Analytics Assignment {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now() - timedelta(days=i*2),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data.update({
                'grading_assignment_id': grading_assignment.id,
                'submission_date': datetime.now() + timedelta(days=7-i)
            })
            assignment = self.op_assignment.create(assignment_data)
            assignment.act_publish()
            assignments.append(assignment)
        
        # Create students for analytics
        students = []
        for i in range(10):
            partner = self.env['res.partner'].create({
                'name': f'Analytics Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            students.append(student)
        
        # Create submissions with varying completion rates and grades
        submission_data = []
        for i, assignment in enumerate(assignments):
            # Different completion rates per assignment
            completion_rate = 0.5 + (i * 0.1)  # 50% to 90% completion
            students_to_submit = int(len(students) * completion_rate)
            
            for j in range(students_to_submit):
                student = students[j]
                # Varying grades based on assignment and student
                base_grade = 70 + (i * 2) + (j % 15)  # Grades 70-100
                
                submission = self.op_assignment_subline.create({
                    'assignment_id': assignment.id,
                    'student_id': student.id,
                    'description': f'Analytics submission {i+1}-{j+1}',
                    'marks': base_grade,
                    'state': 'accept'
                })
                submission_data.append(submission)
        
        # Calculate analytics metrics
        analytics = self._calculate_assignment_analytics(assignments, students, submission_data)
        
        # Verify analytics calculations
        self.assertEqual(analytics['total_assignments'], 5)
        self.assertEqual(analytics['total_students'], 10)
        self.assertGreater(analytics['total_submissions'], 0)
        self.assertGreater(analytics['average_completion_rate'], 0)
        self.assertGreater(analytics['average_grade'], 0)
    
    def _calculate_assignment_analytics(self, assignments, students, submissions):
        """Calculate comprehensive assignment analytics."""
        
        total_assignments = len(assignments)
        total_students = len(students)
        total_submissions = len(submissions)
        
        # Calculate completion rates per assignment
        completion_rates = []
        for assignment in assignments:
            assignment_submissions = [s for s in submissions if s.assignment_id.id == assignment.id]
            completion_rate = len(assignment_submissions) / total_students * 100
            completion_rates.append(completion_rate)
        
        average_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # Calculate grade statistics
        grades = [s.marks for s in submissions if s.marks > 0]
        average_grade = sum(grades) / len(grades) if grades else 0
        max_grade = max(grades) if grades else 0
        min_grade = min(grades) if grades else 0
        
        # Grade distribution
        grade_distribution = {
            'A': len([g for g in grades if g >= 90]),
            'B': len([g for g in grades if 80 <= g < 90]),
            'C': len([g for g in grades if 70 <= g < 80]),
            'D': len([g for g in grades if g < 70])
        }
        
        return {
            'total_assignments': total_assignments,
            'total_students': total_students,
            'total_submissions': total_submissions,
            'average_completion_rate': average_completion_rate,
            'completion_rates': completion_rates,
            'average_grade': average_grade,
            'max_grade': max_grade,
            'min_grade': min_grade,
            'grade_distribution': grade_distribution,
            'submission_rate': (total_submissions / (total_assignments * total_students)) * 100
        }
    
    def test_faculty_performance_report(self):
        """Test faculty performance reporting."""
        
        # Create multiple faculty members
        faculty_members = []
        for i in range(3):
            partner = self.env['res.partner'].create({
                'name': f'Report Faculty {i+1}',
                'is_company': False
            })
            faculty = self.op_faculty.create({
                'partner_id': partner.id
            })
            faculty_members.append(faculty)
        
        # Create assignments for each faculty
        faculty_assignments = {}
        for i, faculty in enumerate(faculty_members):
            assignments = []
            for j in range(2 + i):  # Different workloads
                grading_assignment = self.grading_assignment.create({
                    'name': f'Faculty {i+1} Assignment {j+1}',
                    'course_id': self.course.id,
                    'subject_id': self.subject.id,
                    'issued_date': datetime.now() - timedelta(days=j),
                    'assignment_type': self.assignment_type.id,
                    'faculty_id': faculty.id,
                    'point': 100.0
                })
                
                assignment_data = self.assignment_data.copy()
                assignment_data.update({
                    'grading_assignment_id': grading_assignment.id,
                    'batch_id': self.batch.id
                })
                assignment = self.op_assignment.create(assignment_data)
                assignment.act_publish()
                assignments.append(assignment)
            
            faculty_assignments[faculty.id] = assignments
        
        # Generate faculty performance report
        faculty_report = []
        for faculty in faculty_members:
            assignments = faculty_assignments[faculty.id]
            
            # Calculate faculty metrics
            total_assignments = len(assignments)
            total_submissions = sum(len(a.assignment_sub_line) for a in assignments)
            published_assignments = len([a for a in assignments if a.state == 'publish'])
            
            faculty_metrics = {
                'faculty_id': faculty.id,
                'faculty_name': faculty.name,
                'total_assignments': total_assignments,
                'published_assignments': published_assignments,
                'total_submissions': total_submissions,
                'average_submissions_per_assignment': total_submissions / total_assignments if total_assignments else 0,
                'assignment_states': {
                    'draft': len([a for a in assignments if a.state == 'draft']),
                    'publish': len([a for a in assignments if a.state == 'publish']),
                    'finish': len([a for a in assignments if a.state == 'finish']),
                    'cancel': len([a for a in assignments if a.state == 'cancel'])
                }
            }
            faculty_report.append(faculty_metrics)
        
        # Verify faculty report data
        self.assertEqual(len(faculty_report), 3)
        
        for report in faculty_report:
            self.assertTrue(report['faculty_name'])
            self.assertGreaterEqual(report['total_assignments'], 2)
            self.assertIsInstance(report['assignment_states'], dict)
    
    def test_student_progress_tracking(self):
        """Test student progress tracking and reporting."""
        
        # Create assignments with different due dates
        assignments = []
        for i in range(4):
            deadline = datetime.now() + timedelta(days=i*7)  # Weekly assignments
            grading_assignment = self.grading_assignment.create({
                'name': f'Progress Assignment Week {i+1}',
                'course_id': self.course.id,
                'subject_id': self.subject.id,
                'issued_date': datetime.now() - timedelta(days=1),
                'assignment_type': self.assignment_type.id,
                'faculty_id': self.faculty.id,
                'point': 100.0
            })
            
            assignment_data = self.assignment_data.copy()
            assignment_data.update({
                'grading_assignment_id': grading_assignment.id,
                'submission_date': deadline
            })
            assignment = self.op_assignment.create(assignment_data)
            assignment.act_publish()
            assignments.append(assignment)
        
        # Create student progress scenarios
        students_progress = []
        
        # High performer
        high_performer = self.student1
        for i, assignment in enumerate(assignments):
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': high_performer.id,
                'description': f'High performer submission {i+1}',
                'marks': 90 + i * 2,  # Improving grades
                'state': 'accept'
            })
        
        # Average performer
        average_performer = self.student2
        for i, assignment in enumerate(assignments[:3]):  # Missing one assignment
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': average_performer.id,
                'description': f'Average performer submission {i+1}',
                'marks': 75 + (i % 2) * 5,  # Fluctuating grades
                'state': 'accept'
            })
        
        # Calculate student progress reports
        students_to_track = [high_performer, average_performer]
        progress_reports = []
        
        for student in students_to_track:
            student_submissions = self.op_assignment_subline.search([
                ('student_id', '=', student.id),
                ('assignment_id', 'in', [a.id for a in assignments])
            ])
            
            # Calculate progress metrics
            submitted_count = len(student_submissions)
            total_assignments = len(assignments)
            completion_rate = (submitted_count / total_assignments) * 100
            
            grades = student_submissions.mapped('marks')
            avg_grade = sum(grades) / len(grades) if grades else 0
            
            # Track improvement trend
            if len(grades) >= 2:
                trend = 'improving' if grades[-1] > grades[0] else 'declining' if grades[-1] < grades[0] else 'stable'
            else:
                trend = 'insufficient_data'
            
            progress_report = {
                'student_id': student.id,
                'student_name': student.name,
                'completion_rate': completion_rate,
                'submitted_assignments': submitted_count,
                'total_assignments': total_assignments,
                'average_grade': avg_grade,
                'grades': grades,
                'trend': trend,
                'status': 'on_track' if completion_rate >= 75 and avg_grade >= 75 else 'needs_attention'
            }
            progress_reports.append(progress_report)
        
        # Verify progress tracking
        self.assertEqual(len(progress_reports), 2)
        
        # High performer should be on track
        high_performer_report = next(r for r in progress_reports if r['student_id'] == high_performer.id)
        self.assertEqual(high_performer_report['completion_rate'], 100)
        self.assertEqual(high_performer_report['status'], 'on_track')
        
        # Average performer should need attention (missing assignments)
        average_performer_report = next(r for r in progress_reports if r['student_id'] == average_performer.id)
        self.assertEqual(average_performer_report['completion_rate'], 75)
    
    def test_assignment_timeline_analysis(self):
        """Test assignment timeline and deadline analysis."""
        
        # Create assignments with different timeline patterns
        timeline_assignments = []
        
        # Past assignment (overdue)
        past_assignment = self._create_assignment_with_timeline('Past Assignment', -7, -1)
        timeline_assignments.append(past_assignment)
        
        # Current assignment (due soon)
        current_assignment = self._create_assignment_with_timeline('Current Assignment', -2, 2)
        timeline_assignments.append(current_assignment)
        
        # Future assignment (upcoming)
        future_assignment = self._create_assignment_with_timeline('Future Assignment', 1, 14)
        timeline_assignments.append(future_assignment)
        
        # Analyze timeline patterns
        timeline_analysis = self._analyze_assignment_timeline(timeline_assignments)
        
        # Verify timeline analysis
        self.assertEqual(timeline_analysis['total_assignments'], 3)
        self.assertEqual(timeline_analysis['overdue_assignments'], 1)
        self.assertEqual(timeline_analysis['current_assignments'], 1)
        self.assertEqual(timeline_analysis['upcoming_assignments'], 1)
    
    def _create_assignment_with_timeline(self, name, issue_days_offset, submission_days_offset):
        """Helper method to create assignment with specific timeline."""
        grading_assignment = self.grading_assignment.create({
            'name': name,
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'issued_date': datetime.now() + timedelta(days=issue_days_offset),
            'assignment_type': self.assignment_type.id,
            'faculty_id': self.faculty.id,
            'point': 100.0
        })
        
        assignment_data = self.assignment_data.copy()
        assignment_data.update({
            'grading_assignment_id': grading_assignment.id,
            'submission_date': datetime.now() + timedelta(days=submission_days_offset)
        })
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        return assignment
    
    def _analyze_assignment_timeline(self, assignments):
        """Analyze assignment timeline patterns."""
        now = datetime.now()
        
        overdue = 0
        current = 0
        upcoming = 0
        
        for assignment in assignments:
            if assignment.submission_date < now:
                overdue += 1
            elif assignment.submission_date <= now + timedelta(days=7):
                current += 1
            else:
                upcoming += 1
        
        return {
            'total_assignments': len(assignments),
            'overdue_assignments': overdue,
            'current_assignments': current,
            'upcoming_assignments': upcoming,
            'timeline_distribution': {
                'overdue_percentage': (overdue / len(assignments)) * 100,
                'current_percentage': (current / len(assignments)) * 100,
                'upcoming_percentage': (upcoming / len(assignments)) * 100
            }
        }
    
    def test_grade_distribution_report(self):
        """Test comprehensive grade distribution reporting."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create students with varied performance
        grade_scenarios = [
            (95, 'excellent'),
            (88, 'good'),
            (92, 'excellent'),
            (76, 'satisfactory'),
            (84, 'good'),
            (67, 'needs_improvement'),
            (91, 'excellent'),
            (79, 'satisfactory'),
            (86, 'good'),
            (73, 'satisfactory')
        ]
        
        students_and_grades = []
        for i, (grade, category) in enumerate(grade_scenarios):
            partner = self.env['res.partner'].create({
                'name': f'Grade Distribution Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Grade distribution submission - {category}',
                'marks': grade,
                'state': 'accept'
            })
            students_and_grades.append((student, grade, category))
        
        # Generate grade distribution report
        grade_report = self._generate_grade_distribution_report(assignment)
        
        # Verify distribution
        self.assertEqual(grade_report['total_submissions'], 10)
        self.assertEqual(grade_report['distribution']['excellent'], 3)  # 95, 92, 91
        self.assertEqual(grade_report['distribution']['good'], 3)       # 88, 84, 86
        self.assertEqual(grade_report['distribution']['satisfactory'], 3)  # 76, 79, 73
        self.assertEqual(grade_report['distribution']['needs_improvement'], 1)  # 67
    
    def _generate_grade_distribution_report(self, assignment):
        """Generate comprehensive grade distribution report."""
        submissions = assignment.assignment_sub_line.filtered(lambda s: s.state == 'accept' and s.marks > 0)
        grades = submissions.mapped('marks')
        
        if not grades:
            return {'total_submissions': 0, 'distribution': {}}
        
        # Calculate statistics
        average_grade = sum(grades) / len(grades)
        max_grade = max(grades)
        min_grade = min(grades)
        
        # Grade categories
        excellent = len([g for g in grades if g >= 90])
        good = len([g for g in grades if 80 <= g < 90])
        satisfactory = len([g for g in grades if 70 <= g < 80])
        needs_improvement = len([g for g in grades if g < 70])
        
        return {
            'assignment_id': assignment.id,
            'assignment_name': assignment.name,
            'total_submissions': len(submissions),
            'average_grade': average_grade,
            'max_grade': max_grade,
            'min_grade': min_grade,
            'distribution': {
                'excellent': excellent,
                'good': good,
                'satisfactory': satisfactory,
                'needs_improvement': needs_improvement
            },
            'percentages': {
                'excellent': (excellent / len(grades)) * 100,
                'good': (good / len(grades)) * 100,
                'satisfactory': (satisfactory / len(grades)) * 100,
                'needs_improvement': (needs_improvement / len(grades)) * 100
            }
        }
    
    def test_course_performance_analysis(self):
        """Test course-level performance analysis."""
        
        # Create multiple courses for comparison
        courses = []
        for i in range(3):
            course = self.op_course.create({
                'name': f'Performance Analysis Course {i+1}',
                'code': f'PAC{i+1:02d}'
            })
            courses.append(course)
        
        # Create assignments and submissions for each course
        course_performance_data = {}
        
        for i, course in enumerate(courses):
            # Create batch for course
            batch = self.op_batch.create({
                'name': f'Course {i+1} Batch',
                'course_id': course.id
            })
            
            # Create assignments (different numbers per course)
            assignments = []
            for j in range(2 + i):  # 2, 3, 4 assignments respectively
                grading_assignment = self.grading_assignment.create({
                    'name': f'Course {i+1} Assignment {j+1}',
                    'course_id': course.id,
                    'subject_id': self.subject.id,
                    'issued_date': datetime.now() - timedelta(days=j),
                    'assignment_type': self.assignment_type.id,
                    'faculty_id': self.faculty.id,
                    'point': 100.0
                })
                
                assignment_data = {
                    'grading_assignment_id': grading_assignment.id,
                    'batch_id': batch.id,
                    'marks': 100,
                    'description': f'Course {i+1} assignment {j+1}',
                    'state': 'publish',
                    'submission_date': datetime.now() + timedelta(days=7),
                    'allocation_ids': [(6, 0, [self.student1.id, self.student2.id])]
                }
                
                assignment = self.op_assignment.create(assignment_data)
                assignments.append(assignment)
            
            course_performance_data[course.id] = {
                'course': course,
                'batch': batch,
                'assignments': assignments
            }
        
        # Analyze course performance
        course_analysis = []
        for course_id, data in course_performance_data.items():
            course = data['course']
            assignments = data['assignments']
            
            total_assignments = len(assignments)
            published_assignments = len([a for a in assignments if a.state == 'publish'])
            
            analysis = {
                'course_id': course.id,
                'course_name': course.name,
                'total_assignments': total_assignments,
                'published_assignments': published_assignments,
                'assignment_completion_rate': (published_assignments / total_assignments) * 100 if total_assignments else 0,
                'faculty_engagement': len(set(a.faculty_id.id for a in assignments)),
                'student_allocation': sum(len(a.allocation_ids) for a in assignments)
            }
            course_analysis.append(analysis)
        
        # Verify course analysis
        self.assertEqual(len(course_analysis), 3)
        
        # Check that courses have different assignment counts
        assignment_counts = [analysis['total_assignments'] for analysis in course_analysis]
        expected_counts = [2, 3, 4]
        self.assertEqual(sorted(assignment_counts), sorted(expected_counts))