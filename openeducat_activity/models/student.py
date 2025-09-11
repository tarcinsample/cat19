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

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpStudent(models.Model):
    """Extended student model with comprehensive activity management.
    
    This model extends the base student model to include activity tracking,
    performance analytics, and migration capabilities with proper validation
    and reporting features.
    """
    _inherit = "op.student"

    activity_log = fields.One2many(
        'op.activity', 'student_id',
        string='Activity Log',
        help="All activities participated by this student")
    activity_count = fields.Integer(
        'Activity Count',
        compute='_compute_activity_stats',
        help="Total number of activities for this student")
    active_activity_count = fields.Integer(
        'Active Activity Count', 
        compute='_compute_activity_stats',
        help="Number of active/current activities")
    total_activity_hours = fields.Float(
        'Total Activity Hours',
        compute='_compute_activity_stats',
        help="Total hours spent in activities")
    average_performance_score = fields.Float(
        'Average Performance Score',
        compute='_compute_activity_stats',
        help="Average performance score across all activities")
    last_activity_date = fields.Date(
        'Last Activity Date',
        compute='_compute_activity_stats',
        help="Date of most recent activity")
    activity_categories = fields.Char(
        'Activity Categories',
        compute='_compute_activity_stats',
        help="List of activity categories participated")
    pending_approval_count = fields.Integer(
        'Pending Approvals',
        compute='_compute_activity_stats',
        help="Number of activities pending approval")

    @api.depends('activity_log.active', 'activity_log.duration_hours', 
                 'activity_log.performance_score', 'activity_log.date',
                 'activity_log.activity_category', 'activity_log.state')
    def _compute_activity_stats(self):
        """Compute comprehensive activity statistics for each student."""
        for student in self:
            activities = student.activity_log
            
            # Basic counts
            student.activity_count = len(activities)
            student.active_activity_count = len(activities.filtered('active'))
            student.pending_approval_count = len(
                activities.filtered(lambda a: a.state == 'submitted'))
            
            # Calculate total hours
            total_hours = sum(
                activity.duration_hours or 0 
                for activity in activities
            )
            student.total_activity_hours = total_hours
            
            # Calculate average performance score
            scores = [
                activity.performance_score 
                for activity in activities 
                if activity.performance_score
            ]
            student.average_performance_score = (
                sum(scores) / len(scores) if scores else 0.0
            )
            
            # Get last activity date
            activity_dates = activities.mapped('date')
            student.last_activity_date = max(activity_dates) if activity_dates else False
            
            # Get unique categories
            categories = set(
                activity.activity_category 
                for activity in activities 
                if activity.activity_category
            )
            student.activity_categories = ', '.join(sorted(categories)) if categories else ''

    def get_activity(self):
        """Open view showing all activities for the student.
        
        Returns:
            dict: Action definition to display student activities
        """
        self.ensure_one()
        
        action = self.env.ref('openeducat_activity.'
                              'act_open_op_activity_view').sudo().read()[0]
        action['domain'] = [('student_id', '=', self.id)]
        action['context'] = {
            'default_student_id': self.id,
            'search_default_student_id': self.id
        }
        action['display_name'] = _('Activities - %s') % self.name
        
        return action

    def _compute_count(self):
        """Legacy compute method for backward compatibility."""
        for student in self:
            student.activity_count = len(student.activity_log)

    def create_activity(self, activity_type_id, description, **kwargs):
        """Create a new activity for the student.
        
        Args:
            activity_type_id (int): Activity type ID
            description (str): Activity description
            **kwargs: Additional activity fields
            
        Returns:
            op.activity: Created activity record
        """
        self.ensure_one()
        
        activity_vals = {
            'student_id': self.id,
            'type_id': activity_type_id,
            'description': description,
            'date': kwargs.get('date', fields.Date.today()),
        }
        
        # Add optional fields
        optional_fields = [
            'faculty_id', 'duration_hours', 'location', 
            'achievement', 'performance_score', 'notes'
        ]
        for field in optional_fields:
            if field in kwargs:
                activity_vals[field] = kwargs[field]
        
        activity = self.env['op.activity'].create(activity_vals)
        
        return activity

    def get_activity_summary_by_category(self):
        """Get activity summary grouped by category.
        
        Returns:
            dict: Activity summary by category
        """
        self.ensure_one()
        
        activities = self.activity_log
        summary = {}
        
        for activity in activities:
            category = activity.activity_category or 'other'
            if category not in summary:
                summary[category] = {
                    'count': 0,
                    'total_hours': 0.0,
                    'avg_score': 0.0,
                    'scores': [],
                    'recent_date': False,
                    'approved_count': 0,
                    'completed_count': 0
                }
            
            cat_data = summary[category]
            cat_data['count'] += 1
            
            if activity.duration_hours:
                cat_data['total_hours'] += activity.duration_hours
            
            if activity.performance_score:
                cat_data['scores'].append(activity.performance_score)
            
            if activity.date:
                if not cat_data['recent_date'] or activity.date > cat_data['recent_date']:
                    cat_data['recent_date'] = activity.date
            
            if activity.state == 'approved':
                cat_data['approved_count'] += 1
            elif activity.state == 'completed':
                cat_data['completed_count'] += 1
        
        # Calculate averages
        for cat_data in summary.values():
            if cat_data['scores']:
                cat_data['avg_score'] = sum(cat_data['scores']) / len(cat_data['scores'])
        
        return summary

    def get_activity_performance_trend(self, days=90):
        """Get activity performance trend over specified period.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            dict: Performance trend data
        """
        self.ensure_one()
        
        start_date = fields.Date.subtract(fields.Date.today(), days=days)
        recent_activities = self.activity_log.filtered(
            lambda a: a.date and a.date >= start_date and a.performance_score
        ).sorted('date')
        
        if not recent_activities:
            return {
                'trend': 'no_data',
                'activities': [],
                'average_score': 0.0,
                'score_change': 0.0
            }
        
        # Calculate trend
        scores = [activity.performance_score for activity in recent_activities]
        avg_score = sum(scores) / len(scores)
        
        # Simple trend calculation (first half vs second half)
        mid_point = len(scores) // 2
        if mid_point > 0:
            first_half_avg = sum(scores[:mid_point]) / mid_point
            second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point)
            score_change = second_half_avg - first_half_avg
            
            if score_change > 5:
                trend = 'improving'
            elif score_change < -5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
            score_change = 0.0
        
        return {
            'trend': trend,
            'activities': len(recent_activities),
            'average_score': avg_score,
            'score_change': score_change,
            'period_days': days,
            'activity_data': [
                {
                    'date': activity.date,
                    'score': activity.performance_score,
                    'type': activity.type_id.name,
                    'category': activity.activity_category
                }
                for activity in recent_activities
            ]
        }

    def migrate_to_course(self, new_course_id, new_batch_id=None, migration_date=None):
        """Migrate student to a new course with activity preservation.
        
        Args:
            new_course_id (int): New course ID
            new_batch_id (int): New batch ID (optional)
            migration_date (date): Migration date (optional, defaults to today)
            
        Returns:
            dict: Migration result with status and messages
        """
        self.ensure_one()
        
        if not migration_date:
            migration_date = fields.Date.today()
        
        # Validate new course
        new_course = self.env['op.course'].browse(new_course_id)
        if not new_course.exists():
            raise UserError(_("Invalid course specified for migration."))
        
        # Get current activities that might be affected
        active_activities = self.activity_log.filtered(
            lambda a: a.active and a.state in ('draft', 'submitted', 'approved')
        )
        
        migration_log = {
            'student_id': self.id,
            'old_course': self.course_detail_ids[0].course_id.name if self.course_detail_ids else '',
            'new_course': new_course.name,
            'migration_date': migration_date,
            'active_activities_count': len(active_activities),
            'activities_preserved': [],
            'activities_updated': [],
            'warnings': []
        }
        
        try:
            # Create new course enrollment
            course_vals = {
                'student_id': self.id,
                'course_id': new_course_id,
                'batch_id': new_batch_id,
                'state': 'running'
            }
            
            # End current course enrollment
            current_enrollments = self.course_detail_ids.filtered(
                lambda c: c.state == 'running'
            )
            current_enrollments.write({'state': 'finished'})
            
            # Create new enrollment
            new_enrollment = self.env['op.student.course'].create(course_vals)
            
            # Handle activities
            for activity in active_activities:
                # Check if activity type is compatible with new course
                if activity.type_id.category in ('academic', 'technical'):
                    # Academic activities might need faculty reassignment
                    if new_course.parent_id:  # If course has department
                        dept_faculty = self.env['op.faculty'].search([
                            ('department_id', '=', new_course.parent_id.id)
                        ], limit=1)
                        if dept_faculty and dept_faculty != activity.faculty_id:
                            activity.faculty_id = dept_faculty.id
                            migration_log['activities_updated'].append({
                                'activity_id': activity.id,
                                'activity_name': activity.display_name,
                                'change': f'Faculty updated to {dept_faculty.name}'
                            })
                
                migration_log['activities_preserved'].append({
                    'activity_id': activity.id,
                    'activity_name': activity.display_name,
                    'type': activity.type_id.name,
                    'status': activity.state
                })
            
            # Add note to activities about migration
            migration_note = f"Student migrated from {migration_log['old_course']} to {new_course.name} on {migration_date}"
            for activity in active_activities:
                current_notes = activity.notes or ''
                activity.notes = f"{current_notes}\n{migration_note}".strip()
            
            migration_log['status'] = 'success'
            migration_log['new_enrollment_id'] = new_enrollment.id
            
        except Exception as e:
            migration_log['status'] = 'failed'
            migration_log['error'] = str(e)
            raise UserError(
                _("Migration failed: %s") % str(e)
            )
        
        return migration_log

    def bulk_activity_update(self, activity_ids, update_vals):
        """Bulk update multiple activities for the student.
        
        Args:
            activity_ids (list): List of activity IDs to update
            update_vals (dict): Values to update
            
        Returns:
            dict: Update result with status and messages
        """
        self.ensure_one()
        
        # Validate that all activities belong to this student
        activities = self.env['op.activity'].browse(activity_ids)
        invalid_activities = activities.filtered(
            lambda a: a.student_id.id != self.id
        )
        
        if invalid_activities:
            raise UserError(
                _("Some activities do not belong to student '%s'.") % self.name
            )
        
        # Validate update values
        allowed_fields = [
            'faculty_id', 'location', 'notes', 'achievement', 
            'performance_score', 'state'
        ]
        invalid_fields = [
            field for field in update_vals.keys() 
            if field not in allowed_fields
        ]
        
        if invalid_fields:
            raise UserError(
                _("Cannot update fields: %s. Allowed fields: %s") 
                % (', '.join(invalid_fields), ', '.join(allowed_fields))
            )
        
        # Perform bulk update
        try:
            activities.write(update_vals)
            
            return {
                'status': 'success',
                'updated_count': len(activities),
                'updated_activities': [
                    {
                        'id': activity.id,
                        'name': activity.display_name
                    }
                    for activity in activities
                ]
            }
            
        except Exception as e:
            raise UserError(
                _("Bulk update failed: %s") % str(e)
            )

    def generate_activity_report(self, report_type='comprehensive', date_from=None, date_to=None):
        """Generate comprehensive activity report for the student.
        
        Args:
            report_type (str): Type of report ('summary', 'detailed', 'comprehensive')
            date_from (date): Start date for report
            date_to (date): End date for report
            
        Returns:
            dict: Generated report data
        """
        self.ensure_one()
        
        return self.env['op.activity'].get_student_activity_report(
            self.id, date_from, date_to
        )

    def action_view_activity_analytics(self):
        """Open activity analytics dashboard for the student.
        
        Returns:
            dict: Action definition for analytics view
        """
        self.ensure_one()
        
        return {
            'name': _('Activity Analytics - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'op.activity.analytics.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
                'default_report_type': 'comprehensive'
            }
        }

    def validate_activity_eligibility(self, activity_type_id):
        """Validate if student is eligible for a specific activity type.
        
        Args:
            activity_type_id (int): Activity type ID to validate
            
        Returns:
            dict: Validation result with eligibility status and messages
        """
        self.ensure_one()
        
        activity_type = self.env['op.activity.type'].browse(activity_type_id)
        if not activity_type.exists():
            return {
                'eligible': False,
                'reason': 'Invalid activity type'
            }
        
        warnings = []
        
        # Check if student is active
        if not self.active:
            return {
                'eligible': False,
                'reason': 'Student is not active'
            }
        
        # Check maximum participants limit
        if activity_type.max_participants:
            today_activities = self.env['op.activity'].search([
                ('type_id', '=', activity_type_id),
                ('date', '=', fields.Date.today()),
                ('state', 'not in', ['rejected', 'draft'])
            ])
            
            if len(today_activities) >= activity_type.max_participants:
                return {
                    'eligible': False,
                    'reason': f'Maximum participants ({activity_type.max_participants}) reached for today'
                }
        
        # Check daily activity limit for student
        student_today_activities = self.activity_log.filtered(
            lambda a: a.date == fields.Date.today() and a.state in ('approved', 'completed')
        )
        
        if len(student_today_activities) >= 3:
            warnings.append('Student already has 3 activities today (maximum recommended)')
        
        # Check course compatibility for academic activities
        if activity_type.category == 'academic' and not self.course_detail_ids:
            warnings.append('Student has no active course enrollment')
        
        return {
            'eligible': True,
            'warnings': warnings,
            'activity_type': activity_type.name,
            'requires_approval': activity_type.requires_approval
        }