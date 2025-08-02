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


class OpMediaPurchase(models.Model):
    _name = "op.media.purchase"
    _inherit = "mail.thread"
    _description = "Media Purchase Request"

    name = fields.Char('Title', size=128, required=True)
    request_no = fields.Char('Request No.', readonly=True, copy=False , default='/')
    request_date = fields.Date('Request Date', default=fields.Date.today())
    author = fields.Char(
        'Author(s)', size=256, required=True, tracking=True)
    edition = fields.Char('Edition')
    publisher = fields.Char('Publisher(s)', size=256)
    course_ids = fields.Many2one(
        'op.course', 'Course', required=True, tracking=True)
    subject_ids = fields.Many2one(
        'op.subject', 'Subject', required=True, tracking=True)
    requested_id = fields.Many2one(
        'res.partner', 'Requested By',
        default=lambda self: self.env.user.partner_id.id)
    state = fields.Selection(
        [('draft', 'Draft'), ('request', 'Requested'),
         ('reject', 'Rejected'), ('accept', 'Accepted')],
        'State', readonly=True, default='draft', tracking=True)
    media_type_id = fields.Many2one('op.media.type', 'Media Type')
    active = fields.Boolean(default=True)

    @api.constrains('course_ids', 'subject_ids')
    def _check_course_subject_relation(self):
        """Validate subject belongs to selected course.
        
        Raises:
            ValidationError: If subject doesn't belong to course
        """
        for record in self:
            if record.course_ids and record.subject_ids:
                if record.subject_ids not in record.course_ids.subject_ids:
                    raise ValidationError(_(
                        "Subject '%s' does not belong to course '%s'.") % (
                        record.subject_ids.name, record.course_ids.name))

    def act_requested(self):
        """Submit purchase request for approval.
        
        Validates required fields before submission.
        """
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_(
                "Only draft requests can be submitted."))
        if not self.name or not self.author:
            raise ValidationError(_(
                "Title and author are required to submit request."))
        self.state = 'request'

    def act_accept(self):
        """Accept purchase request.
        
        Validates request state before acceptance.
        """
        self.ensure_one()
        if self.state != 'request':
            raise ValidationError(_(
                "Only submitted requests can be accepted."))
        self.state = 'accept'

    def act_reject(self):
        """Reject purchase request.
        
        Validates request state before rejection.
        """
        self.ensure_one()
        if self.state not in ['request', 'accept']:
            raise ValidationError(_(
                "Only submitted or accepted requests can be rejected."))
        self.state = 'reject'

    @api.onchange('course_ids')
    def onchange_course(self):
        """Update subject domain when course changes."""
        self.subject_ids = False
        if self.course_ids:
            return {
                'domain': {
                    'subject_ids': [('id', 'in', self.course_ids.subject_ids.ids)]
                }
            }
        return {
            'domain': {
                'subject_ids': []
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and validate permissions.
        
        Prevents parent users from creating purchase requests.
        """
        if self.env.user.child_ids:
            raise ValidationError(_(
                'Invalid Action! Parent users cannot create Media Purchase Requests!'))
                
        for vals in vals_list:
            if vals.get('request_no', '/') == '/':
                sequence = self.env['ir.sequence'].next_by_code('op.media.purchase')
                if not sequence:
                    raise ValidationError(_(
                        "Unable to generate purchase request number. "
                        "Please check sequence configuration."))
                vals['request_no'] = sequence
                
        return super(OpMediaPurchase, self).create(vals_list)

    def write(self, vals):
        """Override write to validate permissions and state changes.
        
        Prevents parent users from editing and validates state transitions.
        """
        if self.env.user.child_ids:
            raise ValidationError(_(
                'Invalid Action! Parent users cannot edit Media Purchase Requests!'))
                
        # Prevent editing certain fields after submission
        protected_fields = ['name', 'author', 'course_ids', 'subject_ids']
        if any(field in vals for field in protected_fields):
            for record in self:
                if record.state in ['request', 'accept']:
                    raise ValidationError(_(
                        "Cannot modify request details after submission."))
                        
        return super(OpMediaPurchase, self).write(vals)
        
    def create_media_from_request(self):
        """Create media record from accepted purchase request.
        
        Creates a new media entry based on the purchase request details.
        """
        self.ensure_one()
        
        if self.state != 'accept':
            raise ValidationError(_(
                "Can only create media from accepted purchase requests."))
                
        # Check if media already exists with same name/author
        existing_media = self.env['op.media'].search([
            ('name', '=', self.name),
            ('author_ids.name', 'ilike', self.author)
        ], limit=1)
        
        if existing_media:
            raise ValidationError(_(
                "Media with similar title and author already exists: %s") % 
                existing_media.name)
                
        # Create or get author
        author_names = [name.strip() for name in self.author.split(',')]
        author_ids = []
        for author_name in author_names:
            author = self.env['op.author'].search([('name', '=', author_name)], limit=1)
            if not author:
                author = self.env['op.author'].create({'name': author_name})
            author_ids.append(author.id)
            
        # Create or get publisher if specified
        publisher_ids = []
        if self.publisher:
            publisher_names = [name.strip() for name in self.publisher.split(',')]
            for publisher_name in publisher_names:
                publisher = self.env['op.publisher'].search([('name', '=', publisher_name)], limit=1)
                if not publisher:
                    publisher = self.env['op.publisher'].create({'name': publisher_name})
                publisher_ids.append(publisher.id)
                
        # Create media record
        media_vals = {
            'name': self.name,
            'author_ids': [(6, 0, author_ids)],
            'edition': self.edition,
            'media_type_id': self.media_type_id.id if self.media_type_id else False,
            'course_ids': [(6, 0, [self.course_ids.id])] if self.course_ids else False,
            'subject_ids': [(6, 0, [self.subject_ids.id])] if self.subject_ids else False,
        }
        
        if publisher_ids:
            media_vals['publisher_ids'] = [(6, 0, publisher_ids)]
            
        media = self.env['op.media'].create(media_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Created Media'),
            'res_model': 'op.media',
            'res_id': media.id,
            'view_mode': 'form',
            'target': 'current'
        }
