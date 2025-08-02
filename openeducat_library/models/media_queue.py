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


class OpMediaQueue(models.Model):
    _name = "op.media.queue"
    _inherit = "mail.thread"
    _rec_name = "user_id"
    _description = "Media Queue Request"

    name = fields.Char("Sequence No", readonly=True, copy=False, default='/')
    partner_id = fields.Many2one('res.partner', 'Student/Faculty')
    media_id = fields.Many2one(
        'op.media', 'Media', required=True, tracking=True)
    date_from = fields.Date(
        'From Date', required=True, default=fields.Date.today())
    date_to = fields.Date('To Date', required=True)
    user_id = fields.Many2one(
        'res.users', 'User', readonly=True, default=lambda self: self.env.uid)
    state = fields.Selection(
        [('request', 'Request'), ('accept', 'Accepted'),
         ('reject', 'Rejected')],
        'Status', copy=False, default='request', tracking=True)
    active = fields.Boolean(default=True)

    @api.onchange('user_id')
    def onchange_user(self):
        """Update partner when user changes."""
        if self.user_id:
            self.partner_id = self.user_id.partner_id
        else:
            self.partner_id = False

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        """Validate date range for media queue request.
        
        Raises:
            ValidationError: If date range is invalid
        """
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError(_(
                        "To Date (%s) cannot be set before From Date (%s).") % (
                        record.date_to, record.date_from))
                        
                # Check if request is for future dates
                today = fields.Date.today()
                if record.date_from < today:
                    raise ValidationError(_(
                        "Cannot create queue request for past dates."))

    @api.constrains('media_id', 'date_from', 'date_to')
    def _check_duplicate_request(self):
        """Prevent duplicate queue requests for same media and user.
        
        Raises:
            ValidationError: If duplicate request exists
        """
        for record in self:
            if record.media_id and record.user_id:
                # Check for overlapping requests from same user for same media
                overlapping = self.env['op.media.queue'].search([
                    ('id', '!=', record.id),
                    ('media_id', '=', record.media_id.id),
                    ('user_id', '=', record.user_id.id),
                    ('state', 'in', ['request', 'accept']),
                    ('date_from', '<=', record.date_to),
                    ('date_to', '>=', record.date_from)
                ])
                if overlapping:
                    raise ValidationError(_(
                        "You already have a pending queue request for this media "
                        "during the selected period."))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and validate permissions.
        
        Prevents parent users from creating queue requests.
        """
        if self.env.user.child_ids:
            raise ValidationError(_(
                'Invalid Action! Parent users cannot create Media Queue Requests!'))
                
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                sequence = self.env['ir.sequence'].next_by_code('op.media.queue')
                if not sequence:
                    raise ValidationError(_(
                        "Unable to generate queue request number. "
                        "Please check sequence configuration."))
                vals['name'] = sequence
                
        return super(OpMediaQueue, self).create(vals_list)

    def write(self, vals):
        """Override write to validate permissions.
        
        Prevents parent users from editing queue requests.
        """
        if self.env.user.child_ids:
            raise ValidationError(_(
                'Invalid Action! Parent users cannot edit Media Queue Requests!'))
                
        # Prevent editing certain fields after acceptance
        if 'media_id' in vals or 'date_from' in vals or 'date_to' in vals:
            for record in self:
                if record.state == 'accept':
                    raise ValidationError(_(
                        "Cannot modify media or dates for accepted queue requests."))
                        
        return super(OpMediaQueue, self).write(vals)

    def do_reject(self):
        """Reject queue request.
        
        Sets state to rejected and notifies user.
        """
        for record in self:
            if record.state != 'request':
                raise ValidationError(_(
                    "Only pending requests can be rejected."))
            record.state = 'reject'

    def do_accept(self):
        """Accept queue request.
        
        Validates media availability and accepts request.
        """
        for record in self:
            if record.state != 'request':
                raise ValidationError(_(
                    "Only pending requests can be accepted."))
                    
            # Check if media has available units
            if not record.media_id.check_availability():
                raise ValidationError(_(
                    "Cannot accept request. No available units for media '%s'.") % 
                    record.media_id.name)
                    
            record.state = 'accept'

    def do_request_again(self):
        """Reset request to pending state.
        
        Allows resubmitting rejected requests.
        """
        for record in self:
            if record.state not in ['reject', 'accept']:
                raise ValidationError(_(
                    "Only rejected or accepted requests can be resubmitted."))
            record.state = 'request'
            
    def check_media_availability(self):
        """Check if requested media is available for the date range.
        
        Returns True if media is available, False otherwise.
        """
        self.ensure_one()
        
        # Check if any units are available
        if not self.media_id.available_units:
            return False
            
        # Check for conflicting reservations or issues
        conflicting_movements = self.env['op.media.movement'].search([
            ('media_id', '=', self.media_id.id),
            ('state', 'in', ['issue', 'reserve']),
            ('issued_date', '<=', self.date_to),
            ('return_date', '>=', self.date_from)
        ])
        
        return len(conflicting_movements) < self.media_id.total_units
        
    def create_media_movement(self):
        """Create media movement from accepted queue request.
        
        Creates reservation record for accepted queue request.
        """
        self.ensure_one()
        
        if self.state != 'accept':
            raise ValidationError(_(
                "Can only create movement from accepted queue requests."))
                
        # Get user's library card
        library_card = self.env['op.library.card'].search([
            ('partner_id', '=', self.partner_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not library_card:
            raise ValidationError(_(
                "No active library card found for user '%s'.") % 
                self.partner_id.name)
                
        # Get available media unit
        media_unit = self.media_id.get_next_available_unit()
        if not media_unit:
            raise ValidationError(_(
                "No available units for media '%s'.") % self.media_id.name)
                
        # Create media movement (reservation)
        movement_vals = {
            'media_id': self.media_id.id,
            'media_unit_id': media_unit.id,
            'library_card_id': library_card.id,
            'type': library_card.type,
            'issued_date': self.date_from,
            'return_date': self.date_to,
            'state': 'reserve',
            'partner_id': self.partner_id.id,
            'reserver_name': self.partner_id.name
        }
        
        if library_card.type == 'student':
            movement_vals['student_id'] = library_card.student_id.id
        else:
            movement_vals['faculty_id'] = library_card.faculty_id.id
            
        movement = self.env['op.media.movement'].create(movement_vals)
        media_unit.state = 'reserve'
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Media Reservation'),
            'res_model': 'op.media.movement',
            'res_id': movement.id,
            'view_mode': 'form',
            'target': 'current'
        }
