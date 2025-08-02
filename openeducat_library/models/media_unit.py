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


class OpMediaUnit(models.Model):
    _name = "op.media.unit"
    _inherit = "mail.thread"
    _description = "Media Unit"
    _order = "name"

    name = fields.Char('Name', required=True)
    media_id = fields.Many2one('op.media', 'Media',
                               required=True, tracking=True)
    barcode = fields.Char('Barcode', size=20)
    movement_lines = fields.One2many(
        'op.media.movement', 'media_unit_id', 'Movements')
    state = fields.Selection(
        [('available', 'Available'), ('issue', 'Issued')],
        'State', default='available', tracking=True)
    media_type_id = fields.Many2one(related='media_id.media_type_id',
                                    store=True, string='Media Type')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_name_barcode',
         'unique(barcode)',
         'Barcode must be unique per Media unit!'),
    ]

    current_movement = fields.Many2one('op.media.movement', 'Current Movement',
                                       compute='_compute_current_movement',
                                       help="Current active movement for this unit")
    is_overdue = fields.Boolean('Is Overdue', compute='_compute_overdue_status',
                                help="True if unit is overdue for return")
    
    @api.depends('movement_lines', 'movement_lines.state')
    def _compute_current_movement(self):
        """Compute current active movement for this unit.
        
        Finds the active movement (issued or reserved) for this unit.
        """
        for record in self:
            current = record.movement_lines.filtered(
                lambda m: m.state in ['issue', 'reserve']
            )
            record.current_movement = current[:1] if current else False
    
    @api.depends('current_movement', 'current_movement.is_overdue')
    def _compute_overdue_status(self):
        """Compute overdue status for this unit.
        
        Determines if unit is overdue for return.
        """
        for record in self:
            record.is_overdue = record.current_movement and record.current_movement.is_overdue
    
    @api.constrains('media_id', 'name')
    def _check_unit_name_unique(self):
        """Ensure unit names are unique within media.
        
        Raises:
            ValidationError: If duplicate unit name exists for same media
        """
        for record in self:
            if record.media_id and record.name:
                duplicate = self.env['op.media.unit'].search([
                    ('id', '!=', record.id),
                    ('media_id', '=', record.media_id.id),
                    ('name', '=', record.name)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "Unit name '%s' already exists for media '%s'.") % (
                        record.name, record.media_id.name))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate barcode sequence.
        
        Ensures proper barcode generation with error handling.
        """
        for vals in vals_list:
            sequence = self.env['ir.sequence'].next_by_code('op.media.unit')
            if not sequence:
                raise ValidationError(_(
                    "Unable to generate media unit barcode. "
                    "Please check sequence configuration."))
            vals['barcode'] = sequence
            
        return super(OpMediaUnit, self).create(vals_list)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Enhanced name search to include barcode and media name.
        
        Searches by unit name, barcode, and media name.
        """
        args = args or []
        recs = self.browse()
        
        if name:
            # Search by unit name
            recs = self.search(
                [('name', operator, name)] + args, limit=limit)
            
            # Search by barcode if no results
            if not recs:
                recs = self.search(
                    [('barcode', operator, name)] + args, limit=limit)
            
            # Search by media name if still no results
            if not recs:
                recs = self.search(
                    [('media_id.name', operator, name)] + args, limit=limit)
                    
        return [(res.id, res.display_name) for res in recs]
        
    def check_availability(self):
        """Check if media unit is available for issue.
        
        Returns True if unit is available, False otherwise.
        """
        self.ensure_one()
        return self.state == 'available'
        
    def reserve_unit(self):
        """Reserve this media unit.
        
        Changes state to reserved if available.
        """
        self.ensure_one()
        if not self.check_availability():
            raise ValidationError(_(
                "Media unit '%s' is not available for reservation.") % self.name)
        self.state = 'reserve'
        
    def issue_unit(self):
        """Issue this media unit.
        
        Changes state to issued if available or reserved.
        """
        self.ensure_one()
        if self.state not in ['available', 'reserve']:
            raise ValidationError(_(
                "Media unit '%s' cannot be issued in current state '%s'.") % (
                self.name, self.state))
        self.state = 'issue'
        
    def return_unit(self):
        """Return this media unit.
        
        Changes state back to available if currently issued.
        """
        self.ensure_one()
        if self.state != 'issue':
            raise ValidationError(_(
                "Media unit '%s' is not currently issued.") % self.name)
        self.state = 'available'
        
    def get_unit_history(self):
        """Get movement history for this unit.
        
        Returns action to view all movements for this unit.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unit Movement History - %s') % self.name,
            'res_model': 'op.media.movement',
            'view_mode': 'list,form',
            'domain': [('media_unit_id', '=', self.id)],
            'context': {'default_media_unit_id': self.id},
            'target': 'current'
        }
