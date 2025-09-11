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

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


def days_between(to_date, from_date):
    to_date = fields.Datetime.from_string(to_date)
    from_date = fields.Datetime.from_string(from_date)
    return abs((from_date - to_date).days)


class OpMediaMovement(models.Model):
    _name = "op.media.movement"
    _inherit = "mail.thread"
    _description = "Media Movement"
    _rec_name = "media_id"
    _order = "id DESC"

    media_id = fields.Many2one('op.media', 'Media', required=True)
    media_unit_id = fields.Many2one(
        'op.media.unit', 'Media Unit', required=True,
        tracking=True, domain=[('state', '=', 'available')])
    type = fields.Selection(
        [('student', 'Student'), ('faculty', 'Faculty')],
        'Student/Faculty', required=True)
    student_id = fields.Many2one('op.student', 'Student')
    faculty_id = fields.Many2one('op.faculty', 'Faculty')
    library_card_id = fields.Many2one(
        'op.library.card', 'Library Card', required=True,
        tracking=True)
    issued_date = fields.Date(
        'Issued Date', tracking=True,
        required=True, default=fields.Date.today())
    return_date = fields.Date('Due Date', required=True)
    actual_return_date = fields.Date('Actual Return Date')
    penalty = fields.Float('Penalty')
    partner_id = fields.Many2one(
        'res.partner', 'Person', tracking=True)
    reserver_name = fields.Char('Person Name', size=256)
    state = fields.Selection(
        [('available', 'Available'), ('reserve', 'Reserved'),
         ('issue', 'Issued'), ('lost', 'Lost'),
         ('return', 'Returned'), ('return_done', 'Returned Done')],
        'Status', default='available', tracking=True)
    media_type_id = fields.Many2one(related='media_id.media_type_id',
                                    store=True, string='Media Type')
    user_id = fields.Many2one(
        'res.users', string='Users')
    invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)

    @api.depends('return_date')
    def _compute_overdue_days(self):
        """Compute number of overdue days.
        
        Calculates how many days past due date the media is.
        """
        today = fields.Date.today()
        for record in self:
            if record.return_date and record.state == 'issue':
                if record.return_date < today:
                    record.overdue_days = (today - record.return_date).days
                else:
                    record.overdue_days = 0
            else:
                record.overdue_days = 0
                
    overdue_days = fields.Integer('Overdue Days', compute='_compute_overdue_days',
                                  help="Number of days past due date")
    is_overdue = fields.Boolean('Is Overdue', compute='_compute_overdue_status',
                                help="True if media is overdue for return")
                                
    @api.depends('overdue_days')
    def _compute_overdue_status(self):
        """Compute overdue status.
        
        Determines if media is overdue for return.
        """
        for record in self:
            record.is_overdue = record.overdue_days > 0
            
    def get_diff_day(self):
        """Get difference in days between today and return date.
        
        Legacy method for backward compatibility.
        """
        self.ensure_one()
        return self.overdue_days

    @api.constrains('issued_date', 'return_date')
    def _check_date(self):
        for record in self:
            if record.issued_date > record.return_date:
                raise ValidationError(_(
                    'Return Date cannot be set before Issued Date.'))

    @api.constrains('issued_date', 'actual_return_date')
    def check_actual_return_date(self):
        for record in self:
            if record.actual_return_date:
                if record.issued_date > record.actual_return_date:
                    raise ValidationError(_(
                        'Actual Return Date cannot be set before Issued Date'))

    @api.onchange('media_unit_id')
    def onchange_media_unit_id(self):
        """Update fields when media unit changes."""
        if self.media_unit_id:
            self.state = self.media_unit_id.state
            self.media_id = self.media_unit_id.media_id
            # Check if unit is available for issue
            if self.media_unit_id.state != 'available':
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('Selected media unit is not available for issue.')
                    }
                }

    @api.onchange('library_card_id')
    def onchange_library_card_id(self):
        """Update fields when library card changes."""
        if self.library_card_id:
            self.type = self.library_card_id.type
            
            # Calculate return date
            if self.issued_date:
                duration = self.library_card_id.library_card_type_id.duration or 1
                self.return_date = self.issued_date + timedelta(days=duration)
            
            # Set person details based on card type
            if self.type == 'student' and self.library_card_id.student_id:
                self.student_id = self.library_card_id.student_id
                self.partner_id = self.student_id.partner_id
                self.user_id = self.student_id.user_id
                self.faculty_id = False
            elif self.type == 'faculty' and self.library_card_id.faculty_id:
                self.faculty_id = self.library_card_id.faculty_id
                self.partner_id = self.faculty_id.partner_id
                self.user_id = self.faculty_id.user_id
                self.student_id = False
                
            # Check media limit
            if not self.library_card_id.check_media_limit():
                return {
                    'warning': {
                        'title': _('Media Limit Exceeded'),
                        'message': _('This library card has reached its media limit.')
                    }
                }

    @api.onchange('issued_date')
    def onchange_issued_date(self):
        """Update return date when issued date changes."""
        if self.issued_date and self.library_card_id:
            duration = self.library_card_id.library_card_type_id.duration or 1
            self.return_date = self.issued_date + timedelta(days=duration)

    def issue_media(self):
        """Issue media to library card holder.
        
        Validates availability and updates states.
        """
        for record in self:
            # Validate media unit availability
            if not record.media_unit_id:
                raise ValidationError(_(
                    "Media unit must be selected to issue media."))
            if record.media_unit_id.state != 'available':
                raise ValidationError(_(
                    "Selected media unit is not available for issue."))
                    
            # Validate library card
            if not record.library_card_id:
                raise ValidationError(_(
                    "Library card must be selected to issue media."))
            if not record.library_card_id.check_media_limit():
                raise ValidationError(_(
                    "Library card has reached its media limit."))
                    
            # Check for overdue media
            overdue_media = record.library_card_id.get_overdue_media()
            if overdue_media:
                raise ValidationError(_(
                    "Cannot issue new media. Library card has overdue items."))
                    
            # Issue the media
            record.media_unit_id.state = 'issue'
            record.state = 'issue'

    def return_media(self, return_date=None):
        """Return media and calculate penalties.
        
        Args:
            return_date: Date of return, defaults to today
        """
        for record in self:
            if record.state != 'issue':
                raise ValidationError(_(
                    "Only issued media can be returned."))
                    
            if not return_date:
                return_date = fields.Date.today()
                
            record.actual_return_date = return_date
            record.calculate_penalty()
            
            # Set appropriate state based on penalty
            if record.penalty > 0.0:
                record.state = 'return'  # Pending penalty payment
            else:
                record.state = 'return_done'  # Fully returned
                
            # Make media unit available
            record.media_unit_id.state = 'available'

    def calculate_penalty(self):
        """Calculate penalty amount for overdue return.
        
        Calculates penalty based on overdue days and card type rates.
        """
        for record in self:
            penalty_amt = 0.0
            
            if not record.actual_return_date or not record.return_date:
                record.penalty = penalty_amt
                continue
                
            # Calculate overdue days
            if record.actual_return_date > record.return_date:
                overdue_days = (record.actual_return_date - record.return_date).days
                
                # Calculate penalty amount
                card_type = record.library_card_id.library_card_type_id
                if card_type and overdue_days > 0:
                    penalty_amt = overdue_days * card_type.penalty_amt_per_day
                    
            record.penalty = penalty_amt

    def create_penalty_invoice(self):
        """Create invoice for penalty amount.
        
        Creates accounting invoice for library penalty fees.
        """
        for rec in self:
            if rec.penalty <= 0:
                raise ValidationError(_(
                    "Cannot create invoice for zero penalty amount."))
                    
            if rec.invoice_id:
                raise ValidationError(_(
                    "Invoice already exists for this penalty."))
                    
            # Get penalty product
            try:
                product = self.env.ref('openeducat_library.op_product_7')
            except ValueError:
                raise ValidationError(_(
                    "Library penalty product not found. Please contact administrator."))
                    
            # Determine partner
            partner = rec.partner_id
            if not partner:
                if rec.student_id:
                    partner = rec.student_id.partner_id
                elif rec.faculty_id:
                    partner = rec.faculty_id.partner_id
                else:
                    raise ValidationError(_(
                        "No partner found for penalty invoice."))
                        
            # Get account for penalty product
            account_id = product.property_account_income_id.id
            if not account_id:
                account_id = product.categ_id.property_account_income_categ_id.id
            if not account_id:
                raise UserError(_(
                    'There is no income account defined for penalty product: "%s". '
                    'Please configure the product accounts.') % product.name)

            # Create invoice
            invoice_vals = {
                'partner_id': partner.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': f"Library Penalty - {rec.media_id.name}",
                    'account_id': account_id,
                    'price_unit': rec.penalty,
                    'quantity': 1.0,
                    'discount': 0.0,
                    'product_uom_id': product.uom_id.id,
                    'product_id': product.id,
                })]
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            invoice._compute_tax_totals()
            
            rec.invoice_id = invoice.id
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Penalty Invoice'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current'
            }
