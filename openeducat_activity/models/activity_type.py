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
from odoo.exceptions import ValidationError


class OpActivityType(models.Model):
    """Model for managing activity types in the educational system.
    
    This model defines different categories of student activities such as
    academic, sports, cultural, extracurricular activities with proper
    validation and tracking capabilities.
    """
    _name = "op.activity.type"
    _description = "Activity Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(
        'Activity Type Name', 
        required=True, 
        tracking=True,
        help="Name of the activity type (e.g., Sports, Cultural, Academic)")
    code = fields.Char(
        'Code', 
        size=10,
        tracking=True,
        help="Short code for the activity type")
    description = fields.Text(
        'Description',
        help="Detailed description of the activity type")
    active = fields.Boolean(
        'Active', 
        default=True,
        tracking=True,
        help="Set to False to hide this activity type")
    sequence = fields.Integer(
        'Sequence', 
        default=10,
        help="Sequence order for activity type display")
    color = fields.Integer(
        'Color Index',
        help="Color for visual identification in views")
    category = fields.Selection([
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('social', 'Social Service'),
        ('technical', 'Technical'),
        ('other', 'Other')
    ], string='Category', 
        default='other',
        tracking=True,
        help="Category classification for the activity type")
    requires_approval = fields.Boolean(
        'Requires Approval',
        default=False,
        tracking=True,
        help="Whether activities of this type require faculty approval")
    max_participants = fields.Integer(
        'Maximum Participants',
        help="Maximum number of students allowed for this activity type")
    skill_level = fields.Selection([
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], string='Skill Level',
        help="Required skill level for this activity type")
    duration_hours = fields.Float(
        'Expected Duration (Hours)',
        help="Expected duration in hours for activities of this type")
    activity_count = fields.Integer(
        'Activity Count',
        compute='_compute_activity_count',
        help="Number of activities of this type")
    active_activity_count = fields.Integer(
        'Active Activity Count',
        compute='_compute_activity_count',
        help="Number of active activities of this type")
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 
         'Activity type name must be unique!'),
        ('code_unique', 'unique(code)', 
         'Activity type code must be unique!'),
        ('max_participants_positive', 
         'CHECK (max_participants IS NULL OR max_participants > 0)',
         'Maximum participants must be positive'),
        ('duration_positive',
         'CHECK (duration_hours IS NULL OR duration_hours > 0)',
         'Duration must be positive'),
        ('sequence_positive',
         'CHECK (sequence > 0)',
         'Sequence must be positive')
    ]

    @api.depends('name')
    def _compute_activity_count(self):
        """Compute the number of activities for each activity type."""
        for activity_type in self:
            activities = self.env['op.activity'].search([
                ('type_id', '=', activity_type.id)
            ])
            activity_type.activity_count = len(activities)
            activity_type.active_activity_count = len(
                activities.filtered('active'))

    @api.constrains('name', 'code')
    def _check_name_code_format(self):
        """Validate name and code format."""
        for record in self:
            if record.name:
                if len(record.name.strip()) < 3:
                    raise ValidationError(
                        _("Activity type name must be at least 3 characters long."))
                
                # Check for valid characters
                if not record.name.replace(' ', '').replace('-', '').replace('_', '').isalnum():
                    raise ValidationError(
                        _("Activity type name should contain only letters, numbers, "
                          "spaces, hyphens, and underscores."))
            
            if record.code:
                if len(record.code.strip()) < 2:
                    raise ValidationError(
                        _("Activity type code must be at least 2 characters long."))
                
                if not record.code.replace('-', '').replace('_', '').isalnum():
                    raise ValidationError(
                        _("Activity type code should contain only letters, numbers, "
                          "hyphens, and underscores."))

    @api.constrains('max_participants')
    def _check_max_participants(self):
        """Validate maximum participants constraint."""
        for record in self:
            if record.max_participants and record.max_participants <= 0:
                raise ValidationError(
                    _("Maximum participants must be greater than zero."))
            
            if record.max_participants and record.max_participants > 1000:
                raise ValidationError(
                    _("Maximum participants cannot exceed 1000 students."))

    @api.constrains('duration_hours')
    def _check_duration_hours(self):
        """Validate duration hours constraint."""
        for record in self:
            if record.duration_hours and record.duration_hours <= 0:
                raise ValidationError(
                    _("Duration must be greater than zero hours."))
            
            if record.duration_hours and record.duration_hours > 168:  # 1 week
                raise ValidationError(
                    _("Duration cannot exceed 168 hours (1 week)."))

    @api.onchange('name')
    def _onchange_name(self):
        """Generate code based on name if not set."""
        if self.name and not self.code:
            # Generate code from name (first 3 characters + numbers if needed)
            code = ''.join([c for c in self.name[:6] if c.isalnum()]).upper()
            if len(code) < 2:
                code = 'ACT'
            
            # Check if code exists and append number if needed
            existing = self.search([('code', '=', code)])
            if existing:
                counter = 1
                base_code = code[:3] if len(code) > 3 else code
                while existing:
                    code = f"{base_code}{counter}"
                    existing = self.search([('code', '=', code)])
                    counter += 1
            
            self.code = code

    @api.onchange('category')
    def _onchange_category(self):
        """Update defaults based on category selection."""
        category_defaults = {
            'academic': {
                'requires_approval': True,
                'color': 3,
                'duration_hours': 2.0
            },
            'sports': {
                'requires_approval': False,
                'color': 4,
                'duration_hours': 1.5
            },
            'cultural': {
                'requires_approval': False,
                'color': 5,
                'duration_hours': 3.0
            },
            'social': {
                'requires_approval': True,
                'color': 6,
                'duration_hours': 4.0
            },
            'technical': {
                'requires_approval': True,
                'color': 7,
                'duration_hours': 2.5
            }
        }
        
        if self.category in category_defaults:
            defaults = category_defaults[self.category]
            if not self.requires_approval:
                self.requires_approval = defaults.get('requires_approval', False)
            if not self.color:
                self.color = defaults.get('color', 0)
            if not self.duration_hours:
                self.duration_hours = defaults.get('duration_hours', 2.0)

    def name_get(self):
        """Return activity type name with code and category info."""
        result = []
        for activity_type in self:
            name = activity_type.name
            if activity_type.code:
                name = f"[{activity_type.code}] {name}"
            if activity_type.category:
                category_name = dict(activity_type._fields['category'].selection)[activity_type.category]
                name += f" ({category_name})"
            result.append((activity_type.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search including code and category."""
        if args is None:
            args = []
        
        domain = args.copy()
        if name:
            domain = ['|', '|', 
                     ('name', operator, name),
                     ('code', operator, name),
                     ('category', operator, name)] + domain
        
        return self.search(domain, limit=limit).name_get()

    def action_view_activities(self):
        """Open view showing all activities of this type.
        
        Returns:
            dict: Action definition to display activities
        """
        self.ensure_one()
        
        action = {
            'name': _('Activities - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'op.activity',
            'domain': [('type_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {'default_type_id': self.id}
        }
        
        return action

    def get_activity_statistics(self):
        """Get statistics for activities of this type.
        
        Returns:
            dict: Statistics including counts, participation, etc.
        """
        self.ensure_one()
        
        activities = self.env['op.activity'].search([
            ('type_id', '=', self.id)
        ])
        
        stats = {
            'total_activities': len(activities),
            'active_activities': len(activities.filtered('active')),
            'unique_students': len(activities.mapped('student_id')),
            'unique_faculties': len(activities.mapped('faculty_id')),
            'recent_activities': 0,
            'avg_duration': 0.0
        }
        
        # Count recent activities (last 30 days)
        recent_date = fields.Date.subtract(fields.Date.today(), days=30)
        recent_activities = activities.filtered(
            lambda a: a.date and a.date >= recent_date)
        stats['recent_activities'] = len(recent_activities)
        
        # Calculate average duration if available
        if self.duration_hours:
            stats['avg_duration'] = self.duration_hours
        
        return stats

    @api.model
    def get_activity_types_by_category(self):
        """Get activity types grouped by category.
        
        Returns:
            dict: Activity types grouped by category
        """
        activity_types = self.search([('active', '=', True)], order='category, sequence, name')
        
        categories = {}
        for activity_type in activity_types:
            category = activity_type.category
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': activity_type.id,
                'name': activity_type.name,
                'code': activity_type.code,
                'description': activity_type.description,
                'requires_approval': activity_type.requires_approval,
                'max_participants': activity_type.max_participants,
                'duration_hours': activity_type.duration_hours,
                'activity_count': activity_type.activity_count
            })
        
        return categories

    def validate_activity_type_configuration(self):
        """Validate the complete activity type configuration.
        
        Returns:
            dict: Validation result with status and messages
        """
        self.ensure_one()
        errors = []
        warnings = []
        
        # Check required fields
        if not self.name:
            errors.append(_("Activity type name is required."))
        
        if not self.category:
            warnings.append(_("Activity type category is not set."))
        
        # Check for activities using this type
        if not self.active and self.activity_count > 0:
            warnings.append(
                _("Activity type is inactive but has %d associated activities.") 
                % self.activity_count)
        
        # Check configuration consistency
        if self.requires_approval and not self.description:
            warnings.append(
                _("Activity types requiring approval should have a description."))
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }