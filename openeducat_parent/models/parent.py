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
import logging

_logger = logging.getLogger(__name__)


class OpParent(models.Model):
    """Model for managing parent information and relationships with students.
    
    This model handles parent-student relationships, user management,
    and access control for the parent portal system.
    """
    _name = "op.parent"
    _description = "Parent"
    _rec_name = "name"

    name = fields.Many2one(
        'res.partner', 
        'Name', 
        required=True,
        help="Partner record for the parent",
        tracking=True
    )
    user_id = fields.Many2one(
        'res.users', 
        string='User', 
        store=True,
        help="User account for parent portal access",
        tracking=True
    )
    student_ids = fields.Many2many(
        'op.student', 
        string='Student(s)',
        help="Students associated with this parent"
    )
    mobile = fields.Char(
        string='Mobile', 
        related='name.mobile',
        help="Mobile number from partner record"
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, parent will be archived",
        tracking=True
    )
    relationship_id = fields.Many2one(
        'op.parent.relationship',
        'Relation with Student', 
        required=True,
        help="Type of relationship with the student (e.g., Father, Mother, Guardian)",
        tracking=True
    )
    email = fields.Char(
        string='Email', 
        related='name.email',
        help="Email address from partner record"
    )
    student_count = fields.Integer(
        string='Student Count',
        compute='_compute_student_count',
        help="Number of students associated with this parent"
    )

    _sql_constraints = [(
        'unique_parent',
        'unique(name)',
        'Can not create parent multiple times.!'
    )]

    @api.depends('student_ids')
    def _compute_student_count(self):
        """Compute the number of students associated with this parent."""
        for parent in self:
            parent.student_count = len(parent.student_ids)

    @api.onchange('name')
    def _onchange_name(self):
        """Update user_id when partner name changes.
        
        Automatically links the partner's existing user account
        to the parent record if available.
        """
        if self.name:
            self.user_id = self.name.user_id.id if self.name.user_id else False
        else:
            self.user_id = False

    @api.model_create_multi
    def create(self, vals_list):
        """Create parent records with proper validation and user management.
        
        Args:
            vals_list: List of dictionaries containing parent data
            
        Returns:
            Created parent records
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate data before creation
        for vals in vals_list:
            self._validate_parent_data(vals)
            
        parents = super(OpParent, self).create(vals_list)
        
        # Handle user relationships after creation
        for parent in parents:
            try:
                parent._update_user_relationships()
                _logger.info(f"Created parent record for {parent.name.name}")
            except Exception as e:
                _logger.error(f"Error updating user relationships for parent {parent.id}: {e}")
                raise UserError(_("Failed to establish user relationships. Please check parent configuration."))
                
        return parents

    def write(self, vals):
        """Update parent records with proper validation and user management.
        
        Args:
            vals: Dictionary containing updated values
            
        Returns:
            True if successful
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate data before update
        if any(key in vals for key in ['name', 'relationship_id', 'student_ids']):
            self._validate_parent_data(vals)
            
        res = super(OpParent, self).write(vals)
        
        # Update user relationships if student associations changed
        if 'student_ids' in vals or 'user_id' in vals:
            for parent in self:
                try:
                    parent._update_user_relationships()
                    _logger.info(f"Updated parent record for {parent.name.name}")
                except Exception as e:
                    _logger.error(f"Error updating user relationships for parent {parent.id}: {e}")
                    raise UserError(_("Failed to update user relationships. Please check parent configuration."))
                    
        return res

    def unlink(self):
        """Delete parent records with proper cleanup.
        
        Returns:
            True if successful
            
        Raises:
            UserError: If deletion constraints are violated
        """
        for parent in self:
            # Clean up user relationships before deletion
            try:
                if parent.user_id:
                    parent.user_id.child_ids = [(6, 0, [])]
                    _logger.info(f"Cleaned up user relationships for parent {parent.name.name}")
            except Exception as e:
                _logger.error(f"Error cleaning up parent {parent.id}: {e}")
                raise UserError(_("Failed to clean up parent relationships. Contact administrator."))
                
        return super(OpParent, self).unlink()

    def create_parent_user(self):
        """Create user account for parent portal access.
        
        Creates a user account with appropriate permissions and
        establishes parent-student relationships in the user hierarchy.
        
        Raises:
            ValidationError: If required data is missing or invalid
        """
        try:
            template = self.env.ref('openeducat_parent.parent_template_user', raise_if_not_found=False)
        except Exception:
            template = False
            
        if not template:
            raise ValidationError(_('Parent user template not found. Please contact administrator.'))
            
        users_res = self.env['res.users']
        
        for parent in self:
            # Validate required data
            if not parent.name:
                raise ValidationError(_('Partner name is required to create user account.'))
                
            if not parent.name.email:
                raise ValidationError(_('Email address is required. Please update parent email first.'))
                
            # Check if email is already in use
            existing_user = users_res.search([('login', '=', parent.name.email)], limit=1)
            if existing_user and existing_user != parent.name.user_id:
                raise ValidationError(_('Email address %s is already in use by another user.') % parent.name.email)
                
            if not parent.name.user_id:
                try:
                    # Get student user IDs for child relationship
                    student_user_ids = [
                        student.user_id.id for student in parent.student_ids 
                        if student.user_id and student.user_id.active
                    ]
                    
                    # Create user account
                    user_vals = {
                        'name': parent.name.name,
                        'partner_id': parent.name.id,
                        'login': parent.name.email,
                        'is_parent': True,
                        'tz': self._context.get('tz') or 'UTC',
                        'groups_id': [(6, 0, template.groups_id.ids)] if template.groups_id else [],
                        'child_ids': [(6, 0, student_user_ids)],
                        'active': True
                    }
                    
                    user_id = users_res.create(user_vals)
                    
                    # Update parent and partner records
                    parent.user_id = user_id
                    parent.name.user_id = user_id
                    
                    _logger.info(f"Created user account for parent {parent.name.name}")
                    
                except Exception as e:
                    _logger.error(f"Error creating user for parent {parent.id}: {e}")
                    raise ValidationError(_("Failed to create user account. Please contact administrator."))
            else:
                _logger.info(f"User account already exists for parent {parent.name.name}")

    def _validate_parent_data(self, vals):
        """Validate parent data before creation or update.
        
        Args:
            vals: Dictionary containing parent data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if 'name' in vals:
            partner_id = vals['name']
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                if not partner.exists():
                    raise ValidationError(_('Selected partner does not exist.'))
                    
                # Check if partner is already a parent
                existing_parent = self.search([('name', '=', partner_id), ('id', '!=', self.id)], limit=1)
                if existing_parent:
                    raise ValidationError(_('Partner %s is already registered as a parent.') % partner.name)
                    
        if 'relationship_id' in vals and vals['relationship_id']:
            relationship = self.env['op.parent.relationship'].browse(vals['relationship_id'])
            if not relationship.exists():
                raise ValidationError(_('Selected relationship type does not exist.'))
                
        if 'student_ids' in vals:
            # Validate student relationships
            student_ids = vals['student_ids']
            if isinstance(student_ids, list) and student_ids:
                # Extract actual student IDs from various formats
                actual_student_ids = []
                for item in student_ids:
                    if isinstance(item, (list, tuple)) and len(item) == 3:
                        actual_student_ids.extend(item[2] if item[2] else [])
                    elif isinstance(item, int):
                        actual_student_ids.append(item)
                        
                if actual_student_ids:
                    students = self.env['op.student'].browse(actual_student_ids)
                    invalid_students = students.filtered(lambda s: not s.exists())
                    if invalid_students:
                        raise ValidationError(_('Some selected students do not exist.'))

    def _update_user_relationships(self):
        """Update user parent-child relationships.
        
        Establishes proper user hierarchy for parent portal access.
        """
        if self.user_id and self.student_ids:
            # Get valid student user IDs
            student_user_ids = [
                student.user_id.id for student in self.student_ids 
                if student.user_id and student.user_id.active
            ]
            
            # Update child relationships
            self.user_id.child_ids = [(6, 0, student_user_ids)]
            
    @api.constrains('name', 'relationship_id')
    def _check_parent_relationship_consistency(self):
        """Ensure parent-relationship consistency.
        
        Validates that the parent-student-relationship combination makes sense.
        """
        for parent in self:
            if parent.name and parent.relationship_id:
                # Check for duplicate relationships with same student
                for student in parent.student_ids:
                    other_parents = student.parent_ids.filtered(
                        lambda p: p.id != parent.id and 
                                p.relationship_id.id == parent.relationship_id.id
                    )
                    if other_parents:
                        raise ValidationError(
                            _('Student %s already has a parent with relationship %s.') % 
                            (student.name, parent.relationship_id.name)
                        )

    @api.model
    def get_import_templates(self):
        """Return import templates for parent data.
        
        Returns:
            List of template dictionaries with labels and paths
        """
        return [{
            'label': _('Import Template for Parent'),
            'template': '/openeducat_parent/static/xls/op_parent.xls'
        }]
        
    def action_view_students(self):
        """Open view showing students associated with this parent.
        
        Returns:
            Action dictionary for opening student list view
        """
        action = self.env.ref('openeducat_core.act_open_op_student_view').read()[0]
        action['domain'] = [('parent_ids', 'in', self.ids)]
        action['context'] = {'default_parent_ids': [(6, 0, self.ids)]}
        return action


class OpStudent(models.Model):
    _inherit = "op.student"

    parent_ids = fields.Many2many('op.parent', string='Parent')

    @api.model_create_multi
    def create(self, vals):
        res = super(OpStudent, self).create(vals)
        for values in vals:
            if values.get('parent_ids', False):
                for parent_id in res.parent_ids:
                    if parent_id.user_id:
                        user_ids = [student.user_id.id for student
                                    in parent_id.student_ids if student.user_id]
                        parent_id.user_id.child_ids = [(6, 0, user_ids)]
        return res

    def write(self, vals):
        res = super(OpStudent, self).write(vals)
        if vals.get('parent_ids', False):
            user_ids = []
            if self.parent_ids:
                for parent in self.parent_ids:
                    if parent.user_id:
                        user_ids = [parent.user_id.id for parent in parent.student_ids
                                    if parent.user_id]
                        parent.user_id.child_ids = [(6, 0, user_ids)]
            else:
                user_ids = self.env['res.users'].search([
                    ('child_ids', 'in', self.user_id.id)])
                for user_id in user_ids:
                    child_ids = user_id.child_ids.ids
                    child_ids.remove(self.user_id.id)
                    user_id.child_ids = [(6, 0, child_ids)]
        if vals.get('user_id', False):
            for parent_id in self.parent_ids:
                child_ids = parent_id.user_id.child_ids.ids
                child_ids.append(vals['user_id'])
                parent_id.name.user_id.child_ids = [(6, 0, child_ids)]
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        for record in self:
            if record.parent_ids:
                for parent_id in record.parent_ids:
                    child_ids = parent_id.user_id.child_ids.ids
                    child_ids.remove(record.user_id.id)
                    parent_id.name.user_id.child_ids = [(6, 0, child_ids)]
        return super(OpStudent, self).unlink()

    def get_parent(self):
        action = self.env.ref('openeducat_parent.'
                              'act_open_op_parent_view').sudo().read()[0]
        action['domain'] = [('student_ids', 'in', self.ids)]
        return action


class OpSubjectRegistration(models.Model):
    _inherit = "op.subject.registration"

    @api.model_create_multi
    def create(self, vals):
        if self.env.user.child_ids:
            raise ValidationError(
                _("Invalid action! Parents cannot create subject registrations."))
        return super(OpSubjectRegistration, self).create(vals)

    def write(self, vals):
        if self.env.user.child_ids:
            raise ValidationError(
                _("Invalid action! Parents cannot edit subject registrations."))
        return super(OpSubjectRegistration, self).write(vals)
