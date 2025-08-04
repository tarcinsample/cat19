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

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OpParentRelation(models.Model):
    _name = "op.parent.relationship"
    _description = "Relationships"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    description = fields.Text('Description', help="Description of the relationship type")
    active = fields.Boolean('Active', default=True)
    parent_count = fields.Integer('Parent Count', compute='_compute_parent_count', store=False)

    _sql_constraints = [
        ('unique_relationship_name',
         'unique(name)',
         'Relationship name must be unique!')
    ]

    @api.depends('name')
    def _compute_parent_count(self):
        """Compute the number of parents using this relationship type."""
        for relationship in self:
            relationship.parent_count = self.env['op.parent'].search_count([
                ('relationship_id', '=', relationship.id)
            ])

    @api.constrains('name')
    def _check_name_validity(self):
        """Validate relationship name format and content.
        
        Raises:
            ValidationError: If name is invalid
        """
        for relationship in self:
            if relationship.name:
                # Check minimum length
                if len(relationship.name.strip()) < 2:
                    raise ValidationError(
                        _('Relationship name must be at least 2 characters long.')
                    )
                    
                # Check for invalid characters
                if not relationship.name.replace(' ', '').isalpha():
                    raise ValidationError(
                        _('Relationship name can only contain letters and spaces.')
                    )
                    
    @api.model_create_multi
    def create(self, vals_list):
        """Create relationship records with validation.
        
        Args:
            vals_list: List of dictionaries containing relationship data
            
        Returns:
            Created relationship records
        """
        for vals in vals_list:
            if 'name' in vals and vals['name']:
                vals['name'] = vals['name'].strip().title()
                
        relationships = super(OpParentRelation, self).create(vals_list)
        
        for relationship in relationships:
            _logger.info(f"Created parent relationship type: {relationship.name}")
            
        return relationships
        
    def write(self, vals):
        """Update relationship records with validation.
        
        Args:
            vals: Dictionary containing updated values
            
        Returns:
            True if successful
        """
        if 'name' in vals and vals['name']:
            vals['name'] = vals['name'].strip().title()
            
        res = super(OpParentRelation, self).write(vals)
        
        for relationship in self:
            _logger.info(f"Updated parent relationship type: {relationship.name}")
            
        return res
        
    def unlink(self):
        """Delete relationship records with dependency validation.
        
        Returns:
            True if successful
            
        Raises:
            ValidationError: If relationship is still in use
        """
        for relationship in self:
            parent_count = self.env['op.parent'].search_count([
                ('relationship_id', '=', relationship.id)
            ])
            
            if parent_count > 0:
                raise ValidationError(
                    _('Cannot delete relationship type "%s" as it is currently used by %d parent(s). '
                      'Please reassign or remove the parents first.') % 
                    (relationship.name, parent_count)
                )
                
        return super(OpParentRelation, self).unlink()
        
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search with case-insensitive matching.
        
        Args:
            name: Search term
            args: Additional domain conditions
            operator: Search operator
            limit: Maximum number of results
            
        Returns:
            List of (id, name) tuples
        """
        if args is None:
            args = []
            
        domain = args.copy()
        
        if name:
            domain = ['|', 
                     ('name', operator, name),
                     ('description', operator, name)] + domain
                     
        relationships = self.search(domain, limit=limit)
        return relationships.name_get()
        
    def name_get(self):
        """Return display name with parent count.
        
        Returns:
            List of (id, display_name) tuples
        """
        result = []
        for relationship in self:
            parent_count = self.env['op.parent'].search_count([
                ('relationship_id', '=', relationship.id)
            ])
            
            if parent_count > 0:
                display_name = f"{relationship.name} ({parent_count} parents)"
            else:
                display_name = relationship.name
                
            result.append((relationship.id, display_name))
            
        return result
        
    def action_view_parents(self):
        """Open view showing parents using this relationship type.
        
        Returns:
            Action dictionary for opening parent list view
        """
        action = self.env.ref('openeducat_parent.act_open_op_parent_view').read()[0]
        action['domain'] = [('relationship_id', 'in', self.ids)]
        action['context'] = {
            'default_relationship_id': self.id if len(self) == 1 else False
        }
        return action
