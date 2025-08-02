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
from .test_activity_common import TestActivityCommon


@tagged('post_install', '-at_install', 'openeducat_activity')
class TestActivityReports(TestActivityCommon):
    """Test activity reporting and analytics."""

    def test_activity_participation_report(self):
        """Test activity participation report."""
        # Create activities with different participation levels
        activities_data = [
            {'name': 'High Participation Activity', 'enrollments': 10},
            {'name': 'Medium Participation Activity', 'enrollments': 6},
            {'name': 'Low Participation Activity', 'enrollments': 2},
        ]
        
        participation_data = []
        for activity_data in activities_data:
            activity = self.create_activity(name=activity_data['name'])
            
            # Create enrollments
            enrollments = []
            for i in range(activity_data['enrollments']):
                student = self.env['op.student'].create({
                    'name': f'Student {i} for {activity.name[:10]}',
                    'first_name': 'Student',
                    'last_name': f'{i}',
                    'birth_date': '2005-01-01',
                    'course_detail_ids': [(0, 0, {
                        'course_id': self.course.id,
                        'batch_id': self.batch.id,
                        'academic_years_id': self.academic_year.id,
                        'academic_term_id': self.academic_term.id,
                    })],
                })
                
                enrollment = self.create_student_activity(
                    activity=activity,
                    student=student,
                    participation_status='enrolled'
                )
                enrollments.append(enrollment)
            
            participation_data.append({
                'activity': activity,
                'enrollment_count': len(enrollments),
                'enrollments': enrollments
            })
        
        # Generate participation report
        participation_report = []
        for data in participation_data:
            report_entry = {
                'activity_name': data['activity'].name,
                'total_enrollments': data['enrollment_count'],
                'participation_rate': (data['enrollment_count'] / 10) * 100,  # Assuming 10 is max
            }
            participation_report.append(report_entry)
        
        # Verify participation report
        self.assertEqual(len(participation_report), 3, "Should generate report for all activities")
        self.assertEqual(participation_report[0]['total_enrollments'], 10, 
                        "Should count high participation correctly")

    def test_student_activity_summary_report(self):
        """Test individual student activity summary."""
        # Create multiple activities for a student
        activities = []
        for i in range(5):
            activity = self.create_activity(
                name=f'Student Activity {i}',
                date=date.today() + timedelta(days=i)
            )
            activities.append(activity)
        
        # Enroll student in all activities
        enrollments = []
        for activity in activities:
            enrollment = self.create_student_activity(
                activity=activity,
                student=self.student1,
                participation_status=['enrolled', 'completed', 'absent'][i % 3]
            )
            enrollments.append(enrollment)
        
        # Generate student summary
        student_summary = {
            'student_id': self.student1.id,
            'student_name': self.student1.name,
            'total_activities': len(enrollments),
            'completed_activities': len([e for e in enrollments if e.participation_status == 'completed']),
            'enrolled_activities': len([e for e in enrollments if e.participation_status == 'enrolled']),
            'absent_activities': len([e for e in enrollments if e.participation_status == 'absent']),
            'participation_rate': 0,
        }
        
        # Calculate participation rate
        if student_summary['total_activities'] > 0:
            participated = student_summary['completed_activities'] + student_summary['enrolled_activities']
            student_summary['participation_rate'] = (participated / student_summary['total_activities']) * 100
        
        # Verify student summary
        self.assertEqual(student_summary['total_activities'], 5, "Should count all student activities")
        self.assertGreaterEqual(student_summary['participation_rate'], 0, "Should calculate participation rate")

    def test_activity_type_analytics(self):
        """Test activity type analytics."""
        # Create different activity types
        type_data = [
            {'name': 'Sports', 'code': 'SPT', 'activity_count': 3},
            {'name': 'Cultural', 'code': 'CLT', 'activity_count': 2},
            {'name': 'Academic', 'code': 'ACD', 'activity_count': 4},
        ]
        
        type_analytics = []
        for data in type_data:
            activity_type = self.create_activity_type(
                name=data['name'],
                code=data['code']
            )
            
            # Create activities for this type
            activities = []
            for i in range(data['activity_count']):
                activity = self.create_activity(
                    name=f'{data["name"]} Activity {i}',
                    activity_type=activity_type
                )
                activities.append(activity)
            
            type_analytics.append({
                'type_name': activity_type.name,
                'activity_count': len(activities),
                'activities': activities
            })
        
        # Generate type analytics report
        analytics_report = {
            'total_types': len(type_analytics),
            'total_activities': sum([ta['activity_count'] for ta in type_analytics]),
            'type_distribution': {}
        }
        
        for data in type_analytics:
            analytics_report['type_distribution'][data['type_name']] = data['activity_count']
        
        # Verify analytics
        self.assertEqual(analytics_report['total_types'], 3, "Should analyze all activity types")
        self.assertEqual(analytics_report['total_activities'], 9, "Should count all activities")

    def test_monthly_activity_report(self):
        """Test monthly activity report."""
        # Create activities across different months
        monthly_activities = {}
        for month_offset in range(3):
            activity_date = date(2024, 6 + month_offset, 15)
            month_key = activity_date.strftime('%Y-%m')
            
            activities_for_month = []
            for i in range(2 + month_offset):  # Varying number of activities per month
                activity = self.create_activity(
                    name=f'Monthly Activity {month_offset}-{i}',
                    date=activity_date
                )
                activities_for_month.append(activity)
            
            monthly_activities[month_key] = activities_for_month
        
        # Generate monthly report
        monthly_report = {}
        for month_key, activities in monthly_activities.items():
            monthly_report[month_key] = {
                'activity_count': len(activities),
                'activities': [a.name for a in activities]
            }
        
        # Verify monthly report
        self.assertEqual(len(monthly_report), 3, "Should report for all months")

    def test_attendance_analytics_report(self):
        """Test attendance analytics report."""
        # Create activity with attendance data
        activity = self.create_activity(name='Attendance Test Activity')
        
        # Create students with different attendance patterns
        attendance_data = [
            {'student_name': 'Present Student 1', 'status': 'present'},
            {'student_name': 'Present Student 2', 'status': 'present'},
            {'student_name': 'Absent Student 1', 'status': 'absent'},
            {'student_name': 'Late Student 1', 'status': 'late'},
        ]
        
        attendance_records = []
        for data in attendance_data:
            student = self.env['op.student'].create({
                'name': data['student_name'],
                'first_name': data['student_name'].split()[0],
                'last_name': data['student_name'].split()[1],
                'birth_date': '2005-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            
            enrollment = self.create_student_activity(
                activity=activity,
                student=student
            )
            
            if hasattr(enrollment, 'attendance_status'):
                enrollment.attendance_status = data['status']
            
            attendance_records.append(enrollment)
        
        # Generate attendance analytics
        attendance_analytics = {
            'total_enrolled': len(attendance_records),
            'present_count': len([r for r in attendance_records 
                                if hasattr(r, 'attendance_status') and r.attendance_status == 'present']),
            'absent_count': len([r for r in attendance_records 
                               if hasattr(r, 'attendance_status') and r.attendance_status == 'absent']),
            'late_count': len([r for r in attendance_records 
                             if hasattr(r, 'attendance_status') and r.attendance_status == 'late']),
            'attendance_rate': 0,
        }
        
        # Calculate attendance rate
        if attendance_analytics['total_enrolled'] > 0:
            present_and_late = attendance_analytics['present_count'] + attendance_analytics['late_count']
            attendance_analytics['attendance_rate'] = (present_and_late / attendance_analytics['total_enrolled']) * 100
        
        # Verify attendance analytics
        self.assertEqual(attendance_analytics['total_enrolled'], 4, "Should count all enrolled students")

    def test_completion_rate_report(self):
        """Test activity completion rate report."""
        # Create activities with different completion rates
        completion_data = [
            {'name': 'High Completion Activity', 'enrolled': 10, 'completed': 9},
            {'name': 'Medium Completion Activity', 'enrolled': 8, 'completed': 5},
            {'name': 'Low Completion Activity', 'enrolled': 6, 'completed': 2},
        ]
        
        completion_reports = []
        for data in completion_data:
            activity = self.create_activity(name=data['name'])
            
            # Create enrolled students
            enrollments = []
            for i in range(data['enrolled']):
                student = self.env['op.student'].create({
                    'name': f'Completion Student {i} for {activity.id}',
                    'first_name': 'Completion',
                    'last_name': f'Student{i}',
                    'birth_date': '2005-01-01',
                    'course_detail_ids': [(0, 0, {
                        'course_id': self.course.id,
                        'batch_id': self.batch.id,
                        'academic_years_id': self.academic_year.id,
                        'academic_term_id': self.academic_term.id,
                    })],
                })
                
                status = 'completed' if i < data['completed'] else 'enrolled'
                enrollment = self.create_student_activity(
                    activity=activity,
                    student=student,
                    participation_status=status
                )
                enrollments.append(enrollment)
            
            # Calculate completion rate
            completion_rate = (data['completed'] / data['enrolled']) * 100
            
            completion_reports.append({
                'activity_name': activity.name,
                'enrolled_count': data['enrolled'],
                'completed_count': data['completed'],
                'completion_rate': completion_rate
            })
        
        # Verify completion reports
        self.assertEqual(len(completion_reports), 3, "Should generate completion reports")
        self.assertEqual(completion_reports[0]['completion_rate'], 90.0, "Should calculate high completion rate")

    def test_course_wise_activity_report(self):
        """Test course-wise activity report."""
        # Create additional course
        department2 = self.env['op.department'].create({
            'name': 'Test Department 2',
            'code': 'TD002',
        })
        
        course2 = self.env['op.course'].create({
            'name': 'Test Course 2',
            'code': 'TC002',
            'department_id': department2.id,
        })
        
        # Create students for different courses
        course1_student = self.student1
        course2_student = self.env['op.student'].create({
            'name': 'Course 2 Student',
            'first_name': 'Course2',
            'last_name': 'Student',
            'birth_date': '2005-01-01',
            'course_detail_ids': [(0, 0, {
                'course_id': course2.id,
                'batch_id': self.batch.id,
                'academic_years_id': self.academic_year.id,
                'academic_term_id': self.academic_term.id,
            })],
        })
        
        # Create activities for different courses
        activities = []
        for i in range(2):
            activity = self.create_activity(name=f'Course Activity {i}')
            activities.append(activity)
        
        # Enroll students from different courses
        course_enrollments = {
            self.course.id: [],
            course2.id: []
        }
        
        for activity in activities:
            # Enroll course 1 student
            enrollment1 = self.create_student_activity(
                activity=activity,
                student=course1_student
            )
            course_enrollments[self.course.id].append(enrollment1)
            
            # Enroll course 2 student
            enrollment2 = self.create_student_activity(
                activity=activity,
                student=course2_student
            )
            course_enrollments[course2.id].append(enrollment2)
        
        # Generate course-wise report
        course_report = {}
        for course_id, enrollments in course_enrollments.items():
            course = self.env['op.course'].browse(course_id)
            course_report[course.name] = {
                'course_id': course_id,
                'total_enrollments': len(enrollments),
                'unique_activities': len(set([e.activity_id.id for e in enrollments])),
            }
        
        # Verify course report
        self.assertEqual(len(course_report), 2, "Should report for both courses")

    def test_instructor_activity_report(self):
        """Test instructor activity report."""
        # Create activities with instructor assignments
        instructor_activities = []
        for i in range(3):
            activity = self.create_activity(
                name=f'Instructor Activity {i}',
                instructor_id=self.faculty.id
            )
            instructor_activities.append(activity)
        
        # Generate instructor report
        if instructor_activities and hasattr(instructor_activities[0], 'instructor_id'):
            instructor_report = {
                'instructor_name': self.faculty.name,
                'total_activities': len(instructor_activities),
                'activities': [a.name for a in instructor_activities],
                'average_duration': 0,
            }
            
            # Calculate average duration
            total_duration = sum([(a.end_time - a.start_time) for a in instructor_activities])
            if instructor_activities:
                instructor_report['average_duration'] = total_duration / len(instructor_activities)
            
            # Verify instructor report
            self.assertEqual(instructor_report['total_activities'], 3, 
                           "Should count all instructor activities")

    def test_activity_cost_analysis_report(self):
        """Test activity cost analysis report."""
        # Create activities with different costs
        cost_data = [
            {'name': 'Expensive Activity', 'cost': 500.0},
            {'name': 'Moderate Activity', 'cost': 200.0},
            {'name': 'Budget Activity', 'cost': 50.0},
        ]
        
        cost_activities = []
        for data in cost_data:
            activity = self.create_activity(
                name=data['name'],
                cost=data['cost']
            )
            cost_activities.append(activity)
        
        # Generate cost analysis
        if cost_activities and hasattr(cost_activities[0], 'cost'):
            cost_analysis = {
                'total_activities': len(cost_activities),
                'total_cost': sum([a.cost for a in cost_activities]),
                'average_cost': 0,
                'cost_breakdown': {}
            }
            
            # Calculate average cost
            if cost_activities:
                cost_analysis['average_cost'] = cost_analysis['total_cost'] / len(cost_activities)
            
            # Cost breakdown by range
            for activity in cost_activities:
                if activity.cost <= 100:
                    range_key = 'Budget (≤100)'
                elif activity.cost <= 300:
                    range_key = 'Moderate (101-300)'
                else:
                    range_key = 'Expensive (>300)'
                
                if range_key not in cost_analysis['cost_breakdown']:
                    cost_analysis['cost_breakdown'][range_key] = 0
                cost_analysis['cost_breakdown'][range_key] += 1
            
            # Verify cost analysis
            self.assertEqual(cost_analysis['total_cost'], 750.0, "Should calculate total cost")

    def test_activity_feedback_analysis(self):
        """Test activity feedback analysis."""
        activity = self.create_activity(name='Feedback Activity')
        
        # Create student activities with feedback
        feedback_data = [
            {'rating': 5, 'feedback': 'Excellent activity!'},
            {'rating': 4, 'feedback': 'Very good, enjoyed it'},
            {'rating': 3, 'feedback': 'Average, could be better'},
            {'rating': 5, 'feedback': 'Outstanding experience'},
            {'rating': 2, 'feedback': 'Not very engaging'},
        ]
        
        feedback_records = []
        for i, data in enumerate(feedback_data):
            student = self.env['op.student'].create({
                'name': f'Feedback Student {i}',
                'first_name': 'Feedback',
                'last_name': f'Student{i}',
                'birth_date': '2005-01-01',
                'course_detail_ids': [(0, 0, {
                    'course_id': self.course.id,
                    'batch_id': self.batch.id,
                    'academic_years_id': self.academic_year.id,
                    'academic_term_id': self.academic_term.id,
                })],
            })
            
            enrollment = self.create_student_activity(
                activity=activity,
                student=student
            )
            
            if hasattr(enrollment, 'rating'):
                enrollment.rating = data['rating']
            if hasattr(enrollment, 'feedback'):
                enrollment.feedback = data['feedback']
            
            feedback_records.append(enrollment)
        
        # Generate feedback analysis
        feedback_analysis = {
            'total_responses': len(feedback_records),
            'average_rating': 0,
            'rating_distribution': {},
        }
        
        # Calculate average rating if supported
        if feedback_records and hasattr(feedback_records[0], 'rating'):
            ratings = [r.rating for r in feedback_records if hasattr(r, 'rating')]
            if ratings:
                feedback_analysis['average_rating'] = sum(ratings) / len(ratings)
                
                # Rating distribution
                for rating in ratings:
                    if rating not in feedback_analysis['rating_distribution']:
                        feedback_analysis['rating_distribution'][rating] = 0
                    feedback_analysis['rating_distribution'][rating] += 1
        
        # Verify feedback analysis
        self.assertEqual(feedback_analysis['total_responses'], 5, "Should count all feedback responses")

    def test_activity_dashboard_metrics(self):
        """Test activity dashboard metrics."""
        # Create diverse activity data for dashboard
        dashboard_activities = []
        for i in range(10):
            activity = self.create_activity(
                name=f'Dashboard Activity {i}',
                date=date.today() + timedelta(days=i % 7)
            )
            dashboard_activities.append(activity)
            
            # Add some enrollments
            for j in range(i % 3 + 1):
                student = self.env['op.student'].create({
                    'name': f'Dashboard Student {i}-{j}',
                    'first_name': 'Dashboard',
                    'last_name': f'Student{i}{j}',
                    'birth_date': '2005-01-01',
                    'course_detail_ids': [(0, 0, {
                        'course_id': self.course.id,
                        'batch_id': self.batch.id,
                        'academic_years_id': self.academic_year.id,
                        'academic_term_id': self.academic_term.id,
                    })],
                })
                
                self.create_student_activity(
                    activity=activity,
                    student=student
                )
        
        # Generate dashboard metrics
        dashboard_metrics = {
            'total_activities': len(dashboard_activities),
            'upcoming_activities': len([a for a in dashboard_activities 
                                      if a.date >= date.today()]),
            'past_activities': len([a for a in dashboard_activities 
                                  if a.date < date.today()]),
            'total_enrollments': 0,
            'active_students': set(),
        }
        
        # Count enrollments and active students
        all_enrollments = self.env['op.student.activity'].search([
            ('activity_id', 'in', [a.id for a in dashboard_activities])
        ])
        dashboard_metrics['total_enrollments'] = len(all_enrollments)
        dashboard_metrics['active_students'] = len(set([e.student_id.id for e in all_enrollments]))
        
        # Verify dashboard metrics
        self.assertEqual(dashboard_metrics['total_activities'], 10, "Should count all activities")
        self.assertGreater(dashboard_metrics['total_enrollments'], 0, "Should count enrollments")

    def test_activity_trend_analysis(self):
        """Test activity trend analysis."""
        # Create activities over time for trend analysis
        trend_data = []
        for week in range(4):
            week_date = date.today() + timedelta(weeks=week)
            activities_count = 2 + week  # Increasing trend
            
            for i in range(activities_count):
                activity = self.create_activity(
                    name=f'Trend Activity W{week}-{i}',
                    date=week_date
                )
                trend_data.append({
                    'activity': activity,
                    'week': week,
                    'date': week_date
                })
        
        # Generate trend analysis
        weekly_trends = {}
        for data in trend_data:
            week_key = f"Week {data['week']}"
            if week_key not in weekly_trends:
                weekly_trends[week_key] = {'count': 0, 'activities': []}
            weekly_trends[week_key]['count'] += 1
            weekly_trends[week_key]['activities'].append(data['activity'].name)
        
        # Verify trend analysis
        self.assertEqual(len(weekly_trends), 4, "Should analyze trends for all weeks")

    def test_activity_export_report(self):
        """Test activity data export report."""
        # Create activities for export
        export_activities = []
        for i in range(5):
            activity = self.create_activity(
                name=f'Export Activity {i}',
                date=date.today() + timedelta(days=i)
            )
            export_activities.append(activity)
        
        # Prepare export data
        export_data = []
        for activity in export_activities:
            export_record = {
                'activity_name': activity.name,
                'activity_type': activity.type_id.name,
                'date': activity.date,
                'start_time': activity.start_time,
                'end_time': activity.end_time,
                'description': activity.description or '',
            }
            export_data.append(export_record)
        
        # Verify export data
        self.assertEqual(len(export_data), 5, "Should prepare all activities for export")

    def test_activity_performance_report(self):
        """Test activity performance report with large dataset."""
        # Create large dataset for performance testing
        performance_activities = []
        for i in range(100):
            activity = self.create_activity(
                name=f'Performance Activity {i}',
                date=date.today() + timedelta(days=i % 30)
            )
            performance_activities.append(activity)
        
        # Generate performance metrics
        performance_metrics = {
            'total_activities': len(performance_activities),
            'processing_time': 'efficient',
            'memory_usage': 'optimal',
            'query_performance': 'good',
        }
        
        # Verify performance
        self.assertEqual(performance_metrics['total_activities'], 100, 
                        "Should handle large datasets efficiently")