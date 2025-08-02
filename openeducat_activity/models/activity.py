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
from odoo.exceptions import ValidationError, UserError


class OpActivity(models.Model):
    """Model for managing student activities in the educational system.
    
    This model tracks individual student participation in various activities
    including academic, sports, cultural, and extracurricular events with
    proper validation, approval workflows, and performance tracking.
    """
    _name = "op.activity"
    _description = "Student Activity"
    _rec_name = "display_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, create_date desc"

    def _default_faculty(self):
        """Get default faculty based on current user."""
        return self.env['op.faculty'].search([
            ('user_id', '=', self.env.uid)
        ], limit=1)

    # Core fields
    student_id = fields.Many2one(
        'op.student', 'Student', 
        required=True, 
        tracking=True,
        help="Student participating in this activity")
    faculty_id = fields.Many2one(
        'op.faculty', 'Supervising Faculty',
        default=_default_faculty,
        tracking=True,
        help="Faculty supervising or reporting this activity")
    type_id = fields.Many2one(
        'op.activity.type', 'Activity Type',
        required=True,
        tracking=True,
        help="Type/category of the activity")
    description = fields.Text(
        'Description', 
        required=True,
        tracking=True,
        help="Detailed description of the activity")
    date = fields.Date(
        'Activity Date', 
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date when the activity took place")
    active = fields.Boolean(
        'Active', 
        default=True,
        tracking=True,
        help="Set to False to archive this activity record")

    # Enhanced fields
    display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name showing student and activity details")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], string='Status', 
        default='draft',
        tracking=True,
        help="Current status of the activity")
    duration_hours = fields.Float(
        'Duration (Hours)',
        help="Actual duration of the activity in hours")
    location = fields.Char(
        'Location',
        help="Venue or location where activity took place")
    achievement = fields.Text(
        'Achievement/Result',
        help="Description of achievement or result from the activity")
    performance_score = fields.Float(
        'Performance Score',
        help="Performance score or rating (0-100)")
    notes = fields.Text(
        'Additional Notes',
        help="Additional notes or comments about the activity")
    
    # Computed fields
    course_id = fields.Many2one(
        'op.course', 'Course',
        related='student_id.course_detail_ids.course_id',
        store=True, readonly=True,
        help="Student's current course")
    batch_id = fields.Many2one(
        'op.batch', 'Batch',
        related='student_id.course_detail_ids.batch_id',
        store=True, readonly=True,
        help="Student's current batch")
    requires_approval = fields.Boolean(
        'Requires Approval',
        related='type_id.requires_approval',
        readonly=True,
        help="Whether this activity type requires approval")
    activity_category = fields.Selection(
        related='type_id.category',
        string='Category',
        store=True, readonly=True,
        help="Category of the activity type")
    
    # Dates for workflow
    submitted_date = fields.Datetime(
        'Submitted Date',
        readonly=True,
        help="Date when activity was submitted for approval")
    approved_date = fields.Datetime(
        'Approved Date',
        readonly=True,
        help="Date when activity was approved")
    completed_date = fields.Datetime(
        'Completed Date',
        readonly=True,
        help="Date when activity was marked as completed")

    _sql_constraints = [
        ('performance_score_range',
         'CHECK (performance_score IS NULL OR (performance_score >= 0 AND performance_score <= 100))',
         'Performance score must be between 0 and 100'),
        ('duration_positive',
         'CHECK (duration_hours IS NULL OR duration_hours > 0)',
         'Duration must be positive'),
        ('date_not_future',
         'CHECK (date <= CURRENT_DATE)',
         'Activity date cannot be in the future')
    ]

    @api.depends('student_id', 'type_id', 'date')
    def _compute_display_name(self):
        """Compute display name for the activity."""
        for activity in self:
            parts = []
            if activity.student_id:
                parts.append(activity.student_id.name)
            if activity.type_id:
                parts.append(activity.type_id.name)
            if activity.date:
                parts.append(str(activity.date))
            
            activity.display_name = ' - '.join(parts) if parts else 'New Activity'

    @api.constrains('student_id', 'type_id', 'date')
    def _check_student_activity_limit(self):
        """Check if student exceeds activity limit for the type."""
        for activity in self:
            if activity.type_id and activity.type_id.max_participants:
                # Check if this type has participant limit per date
                same_day_activities = self.search([
                    ('type_id', '=', activity.type_id.id),
                    ('date', '=', activity.date),
                    ('state', 'not in', ['rejected', 'draft']),
                    ('id', '!=', activity.id)
                ])
                
                if len(same_day_activities) >= activity.type_id.max_participants:
                    raise ValidationError(
                        _("Maximum participants (%d) exceeded for activity type '%s' on %s.") 
                        % (activity.type_id.max_participants, 
                           activity.type_id.name, 
                           activity.date))

    @api.constrains('student_id', 'date')
    def _check_student_availability(self):
        """Check if student is available on the activity date."""
        for activity in self:
            if activity.student_id and activity.date:
                # Check for conflicting activities on same date
                conflicting = self.search([
                    ('student_id', '=', activity.student_id.id),
                    ('date', '=', activity.date),
                    ('state', 'in', ['approved', 'completed']),
                    ('id', '!=', activity.id)
                ])
                
                if len(conflicting) > 2:  # Allow max 3 activities per day
                    raise ValidationError(
                        _("Student '%s' already has too many activities on %s. "
                          "Maximum 3 activities per day allowed.") 
                        % (activity.student_id.name, activity.date))

    @api.constrains('performance_score')
    def _check_performance_score(self):
        """Validate performance score range."""
        for activity in self:
            if activity.performance_score is not False:  # Allow 0 score
                if not (0 <= activity.performance_score <= 100):
                    raise ValidationError(
                        _("Performance score must be between 0 and 100. "
                          "Current value: %s") % activity.performance_score)

    @api.onchange('student_id')
    def _onchange_student_id(self):
        """Update related fields when student changes."""
        if self.student_id:
            # Set faculty based on student's current course/batch if available
            if self.student_id.course_detail_ids:
                course_detail = self.student_id.course_detail_ids[0]
                if course_detail.course_id.parent_id:  # If course has department
                    # Try to find a faculty from the same department
                    dept_faculty = self.env['op.faculty'].search([
                        ('department_id', '=', course_detail.course_id.parent_id.id)
                    ], limit=1)
                    if dept_faculty:
                        self.faculty_id = dept_faculty.id

    @api.onchange('type_id')
    def _onchange_type_id(self):
        """Update fields based on activity type selection."""
        if self.type_id:
            # Set default duration from activity type
            if self.type_id.duration_hours and not self.duration_hours:
                self.duration_hours = self.type_id.duration_hours
            
            # Set initial state based on approval requirement
            if self.type_id.requires_approval and self.state == 'draft':
                # Keep as draft, will need to be submitted
                pass
            elif not self.type_id.requires_approval:
                # Auto-approve if no approval required
                self.state = 'approved'

    @api.onchange('date')
    def _onchange_date(self):
        """Validate activity date."""
        if self.date and self.date > fields.Date.today():
            return {
                'warning': {
                    'title': _('Future Date Warning'),
                    'message': _('Activity date is in the future. '
                               'Activities should typically be recorded after completion.')
                }
            }

    def action_submit(self):
        """Submit activity for approval."""
        for activity in self:
            if activity.state != 'draft':
                raise UserError(
                    _("Only draft activities can be submitted. "
                      "Current state: %s") % activity.state)
            
            if not activity.description.strip():
                raise UserError(
                    _("Activity description is required before submission."))
            
            activity.write({
                'state': 'submitted',
                'submitted_date': fields.Datetime.now()
            })

    def action_approve(self):
        """Approve submitted activity."""
        for activity in self:
            if activity.state != 'submitted':
                raise UserError(
                    _("Only submitted activities can be approved. "
                      "Current state: %s") % activity.state)
            
            # Check if current user can approve
            if not self.env.user.has_group('openeducat_core.group_op_faculty'):
                raise UserError(
                    _("Only faculty members can approve activities."))
            
            activity.write({
                'state': 'approved',
                'approved_date': fields.Datetime.now()
            })

    def action_reject(self):
        """Reject submitted activity."""
        for activity in self:
            if activity.state not in ('submitted', 'approved'):
                raise UserError(
                    _("Only submitted or approved activities can be rejected. "
                      "Current state: %s") % activity.state)
            
            activity.write({
                'state': 'rejected',
                'approved_date': False  # Clear approval date
            })

    def action_complete(self):
        """Mark activity as completed."""
        for activity in self:
            if activity.state != 'approved':
                raise UserError(
                    _("Only approved activities can be marked as completed. "
                      "Current state: %s") % activity.state)
            
            activity.write({
                'state': 'completed',
                'completed_date': fields.Datetime.now()
            })

    def action_reset_to_draft(self):
        """Reset activity to draft state."""
        for activity in self:
            if activity.state == 'completed':
                raise UserError(
                    _("Completed activities cannot be reset to draft."))
            
            activity.write({
                'state': 'draft',
                'submitted_date': False,
                'approved_date': False,
                'completed_date': False
            })

    def get_activity_summary(self):
        """Get summary information for the activity.
        
        Returns:
            dict: Activity summary with key information
        """
        self.ensure_one()
        
        return {
            'student_name': self.student_id.name,
            'student_id': self.student_id.student_id,
            'activity_type': self.type_id.name,
            'category': self.activity_category,
            'date': self.date,
            'duration': self.duration_hours,
            'location': self.location,
            'status': self.state,
            'performance_score': self.performance_score,
            'achievement': self.achievement,
            'supervising_faculty': self.faculty_id.name if self.faculty_id else '',
            'course': self.course_id.name if self.course_id else '',
            'batch': self.batch_id.name if self.batch_id else ''
        }

    @api.model
    def get_student_activity_report(self, student_id, date_from=None, date_to=None):
        """Generate activity report for a student.
        
        Args:
            student_id (int): Student ID
            date_from (date): Start date for report
            date_to (date): End date for report
            
        Returns:
            dict: Comprehensive activity report
        """
        domain = [('student_id', '=', student_id)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        
        activities = self.search(domain, order='date desc')
        
        # Group activities by category
        by_category = {}
        total_hours = 0.0
        performance_scores = []
        
        for activity in activities:
            category = activity.activity_category or 'other'
            if category not in by_category:
                by_category[category] = {
                    'count': 0,
                    'hours': 0.0,
                    'activities': []
                }
            
            by_category[category]['count'] += 1
            if activity.duration_hours:
                by_category[category]['hours'] += activity.duration_hours
                total_hours += activity.duration_hours
            
            if activity.performance_score:
                performance_scores.append(activity.performance_score)
            
            by_category[category]['activities'].append(activity.get_activity_summary())
        
        # Calculate statistics
        avg_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0.0
        
        return {
            'student_id': student_id,
            'student_name': activities[0].student_id.name if activities else '',
            'total_activities': len(activities),
            'total_hours': total_hours,
            'average_performance': avg_performance,
            'by_category': by_category,
            'date_range': {
                'from': date_from,
                'to': date_to
            },
            'recent_activities': [a.get_activity_summary() for a in activities[:5]]
        }

    @api.model
    def get_activity_analytics(self, group_by='category', date_from=None, date_to=None):
        """Get activity analytics grouped by specified field.
        
        Args:
            group_by (str): Field to group by ('category', 'type_id', 'faculty_id')
            date_from (date): Start date for analysis
            date_to (date): End date for analysis
            
        Returns:
            dict: Analytics data grouped by specified field
        """
        domain = [('active', '=', True)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        
        activities = self.search(domain)
        
        # Group activities
        groups = {}
        for activity in activities:
            if group_by == 'category':
                key = activity.activity_category or 'other'
                name = dict(activity._fields['activity_category'].selection).get(key, 'Other')
            elif group_by == 'type_id':
                key = activity.type_id.id
                name = activity.type_id.name
            elif group_by == 'faculty_id':
                key = activity.faculty_id.id if activity.faculty_id else 0
                name = activity.faculty_id.name if activity.faculty_id else 'No Faculty'
            else:
                key = 'all'
                name = 'All Activities'
            
            if key not in groups:
                groups[key] = {
                    'name': name,
                    'count': 0,
                    'students': set(),
                    'total_hours': 0.0,
                    'avg_performance': 0.0,
                    'scores': []
                }
            
            groups[key]['count'] += 1
            groups[key]['students'].add(activity.student_id.id)
            if activity.duration_hours:
                groups[key]['total_hours'] += activity.duration_hours
            if activity.performance_score:
                groups[key]['scores'].append(activity.performance_score)
        
        # Calculate averages
        for group_data in groups.values():
            group_data['unique_students'] = len(group_data['students'])
            group_data['students'] = list(group_data['students'])  # Convert set to list
            if group_data['scores']:
                group_data['avg_performance'] = sum(group_data['scores']) / len(group_data['scores'])
        
        return groups

    def validate_activity_data(self):
        """Validate activity data completeness and consistency.
        
        Returns:
            dict: Validation result with status and messages
        """
        self.ensure_one()
        errors = []
        warnings = []
        
        # Check required data
        if not self.description or not self.description.strip():
            errors.append(_("Activity description is required."))
        
        if not self.date:
            errors.append(_("Activity date is required."))
        
        # Check data consistency
        if self.performance_score and not self.achievement:
            warnings.append(_("Performance score provided but no achievement description."))
        
        if self.state in ('approved', 'completed') and not self.faculty_id:
            warnings.append(_("Approved/completed activities should have supervising faculty."))
        
        # Check for potential duplicates
        similar_activities = self.search([
            ('student_id', '=', self.student_id.id),
            ('type_id', '=', self.type_id.id),
            ('date', '=', self.date),
            ('id', '!=', self.id)
        ])
        if similar_activities:
            warnings.append(_("Similar activity found for same student on same date."))
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }