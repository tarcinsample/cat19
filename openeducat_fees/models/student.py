##############################################################################
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
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class OpStudentFeesDetails(models.Model):
    _name = "op.student.fees.details"
    _description = "Student Fees Details"
    _rec_name = 'student_id'

    fees_line_id = fields.Many2one('op.fees.terms.line', 'Fees Line')
    invoice_id = fields.Many2one('account.move', 'Invoice ID')
    amount = fields.Monetary('Fees Amount', currency_field='currency_id')
    date = fields.Date('Submit Date')
    product_id = fields.Many2one('product.product', 'Product')
    student_id = fields.Many2one('op.student', 'Student', required=True)
    fees_factor = fields.Float("Fees Factor")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invoice', 'Invoice Created'),
        ('cancel', 'Cancel')
    ], string='Status', copy=False)
    invoice_state = fields.Selection(related="invoice_id.state",
                                     string='Invoice Status',
                                     readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    after_discount_amount = fields.Monetary(compute="_compute_discount_amount",
                                            currency_field='currency_id',
                                            string='After Discount Amount')
    discount = fields.Float(string='Discount (%)',
                            digits='Discount', default=0.0)

    course_id = fields.Many2one('op.course', 'Course', required=False)
    batch_id = fields.Many2one('op.batch', 'Batch', required=False)

    @api.depends('discount')
    def _compute_discount_amount(self):
        for discount in self:
            discount_amount = discount.amount * discount.discount / 100.0
            discount.after_discount_amount = discount.amount - discount_amount

    @api.depends('company_id')
    def _compute_currency_id(self):
        main_company = self.env['res.company']._get_main_company()
        for template in self:
            template.currency_id = \
                template.company_id.sudo().currency_id.id or main_company.currency_id.id

    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency', 
        compute='_compute_currency_id',
        store=True,
        default=lambda self: self.env.user.company_id.currency_id,
        help="Currency for this fee payment")
    
    _sql_constraints = [
        ('amount_positive', 'CHECK (amount > 0)', 
         'Fee amount must be positive.'),
        ('discount_valid', 'CHECK (discount >= 0 AND discount <= 100)', 
         'Discount must be between 0% and 100%.'),
        ('fees_factor_positive', 'CHECK (fees_factor > 0)', 
         'Fees factor must be positive.'),
    ]
    
    @api.constrains('amount', 'discount')
    def _check_amounts(self):
        """Validate amount and discount values."""
        for record in self:
            if record.amount <= 0:
                raise ValidationError(
                    _("Fee amount must be greater than zero."))
            if not (0 <= record.discount <= 100):
                raise ValidationError(
                    _("Discount percentage must be between 0 and 100."))
    
    @api.constrains('student_id', 'product_id', 'date')
    def _check_student_fee_uniqueness(self):
        """Ensure no duplicate fee records for same student/product/date."""
        for record in self:
            if record.student_id and record.product_id and record.date:
                existing = self.search([
                    ('student_id', '=', record.student_id.id),
                    ('product_id', '=', record.product_id.id),
                    ('date', '=', record.date),
                    ('state', '!=', 'cancel'),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _("A fee record already exists for student '%s' "
                          "with product '%s' on date %s.") % (
                            record.student_id.name,
                            record.product_id.name,
                            record.date))
    
    @api.onchange('student_id')
    def _onchange_student_id(self):
        """Update course and batch when student changes."""
        if self.student_id:
            if self.student_id.course_detail_ids:
                latest_course = self.student_id.course_detail_ids[0]
                self.course_id = latest_course.course_id
                self.batch_id = latest_course.batch_id
    
    @api.onchange('discount')
    def _onchange_discount(self):
        """Validate discount percentage on change."""
        if self.discount < 0 or self.discount > 100:
            return {
                'warning': {
                    'title': _('Invalid Discount'),
                    'message': _('Discount percentage must be between 0 and 100.')
                }
            }

    def get_invoice(self):
        """Create invoice for fee payment process of student.
        
        This method generates an invoice for the student fee payment,
        handling product-based billing and fee elements if configured.
        
        Returns:
            bool: True if invoice is successfully created
            
        Raises:
            UserError: If required account configuration is missing
            ValidationError: If amount or product validation fails
        """
        self.ensure_one()
        
        # Validate prerequisites
        if self.state != 'draft':
            raise UserError(
                _("Cannot create invoice for fee detail in '%s' state. "
                  "Only draft records can be invoiced.") % self.state)
        
        if self.invoice_id:
            raise UserError(
                _("Invoice already exists for this fee detail. "
                  "Use 'View Invoice' to access the existing invoice."))
        
        if not self.student_id.partner_id:
            raise UserError(
                _("Student '%s' has no partner associated. "
                  "Please complete student setup first.") % self.student_id.name)
        
        inv_obj = self.env['account.move']
        partner_id = self.student_id.partner_id
        product = self.product_id
        
        # Get income account for the product
        account_id = self._get_product_income_account(product)
        
        # Validate amount
        if self.amount <= 0.00:
            raise UserError(
                _('The fee amount must be positive. Current amount: %s') 
                % self.amount)
        
        # Prepare invoice lines
        invoice_line_list = self._prepare_invoice_lines(account_id)
        
        try:
            # Create invoice with proper error handling
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner_id.id,
                'invoice_line_ids': invoice_line_list,
                'ref': _('Student Fee - %s') % self.student_id.name,
                'invoice_origin': _('Fee Payment - %s') % self.display_name,
                'company_id': self.company_id.id,
            }
            
            # Add course and batch reference if available
            if self.course_id:
                invoice_vals['ref'] += f' - {self.course_id.name}'
            if self.batch_id:
                invoice_vals['ref'] += f' ({self.batch_id.name})'
            
            invoice = inv_obj.create(invoice_vals)
            invoice._compute_tax_totals()
            
            # Update fee detail state
            self.write({
                'state': 'invoice',
                'invoice_id': invoice.id
            })
            
            return True
            
        except Exception as e:
            raise UserError(
                _("Failed to create invoice: %s") % str(e)
            )

    def _get_product_income_account(self, product):
        """Get the income account for the product.
        
        Args:
            product: Product record
            
        Returns:
            int: Account ID
            
        Raises:
            UserError: If no account is found
        """
        account_id = False
        
        # Try product's income account first
        if product.property_account_income_id:
            account_id = product.property_account_income_id.id
        
        # Try category's income account
        if not account_id and product.categ_id:
            if product.categ_id.property_account_income_categ_id:
                account_id = product.categ_id.property_account_income_categ_id.id
        
        # Try default income account from fiscal position
        if not account_id:
            fiscal_position = self.student_id.partner_id.property_account_position_id
            if fiscal_position:
                account_id = fiscal_position.map_account(
                    self.env.company.account_default_pos_receivable_account_id
                ).id
        
        if not account_id:
            raise UserError(
                _('No income account defined for product "%s". '
                  'Please configure the income account in product settings '
                  'or product category settings.') % product.name)
        
        return account_id

    def _prepare_invoice_lines(self, account_id):
        """Prepare invoice lines based on fee elements or direct product.
        
        Args:
            account_id (int): Income account ID
            
        Returns:
            list: Invoice line commands
        """
        invoice_line_list = []
        
        # Check if fee elements exist for detailed billing
        element_ids = self.env['op.fees.element'].search([
            ('fees_terms_line_id', '=', self.fees_line_id.id),
            ('active', '=', True)
        ]) if self.fees_line_id else self.env['op.fees.element']
        
        if element_ids:
            # Create invoice lines from fee elements
            total_percentage = sum(element_ids.mapped('value'))
            if total_percentage != 100:
                raise UserError(
                    _("Fee elements percentages must sum to 100%%. "
                      "Current total: %.2f%%") % total_percentage)
            
            for element in element_ids:
                line_amount = (element.value * self.amount) / 100
                
                # Apply discount if applicable
                discount_amount = 0.0
                if self.discount:
                    discount_amount = (line_amount * self.discount) / 100
                
                invoice_line_list.append((0, 0, {
                    'name': element.product_id.name,
                    'account_id': self._get_product_income_account(element.product_id),
                    'price_unit': line_amount,
                    'quantity': 1.0,
                    'discount': self.discount or 0.0,
                    'product_uom_id': element.product_id.uom_id.id,
                    'product_id': element.product_id.id,
                }))
        else:
            # Create single invoice line for direct product billing
            invoice_line_list.append((0, 0, {
                'name': self.product_id.name,
                'account_id': account_id,
                'price_unit': self.amount,
                'quantity': 1.0,
                'discount': self.discount or 0.0,
                'product_uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id
            }))
        
        return invoice_line_list

    def action_get_invoice(self):
        value = True
        if self.invoice_id:
            form_view = self.env.ref('account.view_move_form')
            tree_view = self.env.ref('account.view_invoice_tree')
            value = {
                'domain': str([('id', '=', self.invoice_id.id)]),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': False,
                'views': [(form_view and form_view.id or False, 'form'),
                          (tree_view and tree_view.id or False, 'tree')],
                'type': 'ir.actions.act_window',
                'res_id': self.invoice_id.id,
                'target': 'current',
                'nodestroy': True
            }
        return value


class OpStudent(models.Model):
    """Extended student model with fees management capabilities.
    
    This model extends the base student model to include comprehensive
    fees management functionality, including fee tracking, payment
    monitoring, and invoice management.
    """
    _inherit = "op.student"

    fees_detail_ids = fields.One2many(
        'op.student.fees.details',
        'student_id',
        string='Fees Collection Details',
        tracking=True,
        help="All fee payment records for this student")
    fees_details_count = fields.Integer(
        compute='_compute_fees_details',
        string='Fees Count',
        help="Total number of fee records for this student")
    total_fees_amount = fields.Monetary(
        compute='_compute_total_fees',
        string='Total Fees Amount',
        currency_field='currency_id',
        help="Total amount of all fees for this student")
    paid_fees_amount = fields.Monetary(
        compute='_compute_total_fees',
        string='Paid Fees Amount',
        currency_field='currency_id',
        help="Total amount of paid fees")
    pending_fees_amount = fields.Monetary(
        compute='_compute_total_fees',
        string='Pending Fees Amount',
        currency_field='currency_id',
        help="Total amount of pending fees")
    fees_payment_percentage = fields.Float(
        compute='_compute_total_fees',
        string='Payment Percentage',
        help="Percentage of fees paid")
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Currency')

    @api.depends('fees_detail_ids')
    def _compute_fees_details(self):
        """Compute the count of fee details for each student."""
        for student in self:
            student.fees_details_count = len(student.fees_detail_ids)
    
    @api.depends('fees_detail_ids.amount', 'fees_detail_ids.state', 
                 'fees_detail_ids.after_discount_amount')
    def _compute_total_fees(self):
        """Compute total fees amounts and payment percentage."""
        for student in self:
            total_amount = 0.0
            paid_amount = 0.0
            
            for fee_detail in student.fees_detail_ids:
                if fee_detail.state != 'cancel':
                    fee_amount = fee_detail.after_discount_amount or fee_detail.amount
                    total_amount += fee_amount
                    
                    if fee_detail.state in ('paid', 'invoice') and fee_detail.invoice_id:
                        if fee_detail.invoice_id.payment_state == 'paid':
                            paid_amount += fee_amount
            
            student.total_fees_amount = total_amount
            student.paid_fees_amount = paid_amount
            student.pending_fees_amount = total_amount - paid_amount
            
            if total_amount > 0:
                student.fees_payment_percentage = (paid_amount / total_amount) * 100
            else:
                student.fees_payment_percentage = 0.0

    def action_view_invoice(self):
        """Open view showing all invoices related to student fees.
        
        Returns:
            dict: Action definition to display student invoices
        """
        self.ensure_one()
        
        # Get all invoice IDs from fees details
        invoice_ids = self.fees_detail_ids.mapped('invoice_id').ids
        
        if not invoice_ids:
            raise UserError(
                _("No invoices found for student '%s'.") % self.name)
        
        action = {
            'name': _('Student Fee Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_move_type': 'out_invoice'
            }
        }
        
        if len(invoice_ids) == 1:
            action.update({
                'res_id': invoice_ids[0],
                'view_mode': 'form',
                'target': 'current'
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'target': 'current'
            })
        
        return action
    
    def action_view_fees_details(self):
        """Open view showing all fee details for the student.
        
        Returns:
            dict: Action definition to display fee details
        """
        self.ensure_one()
        
        return {
            'name': _('Student Fee Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'op.student.fees.details',
            'domain': [('student_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {'default_student_id': self.id}
        }
    
    def get_fees_summary(self):
        """Get a summary of student's fees status.
        
        Returns:
            dict: Dictionary containing fees summary information
        """
        self.ensure_one()
        
        summary = {
            'total_fees': self.total_fees_amount,
            'paid_fees': self.paid_fees_amount,
            'pending_fees': self.pending_fees_amount,
            'payment_percentage': self.fees_payment_percentage,
            'total_records': self.fees_details_count,
            'overdue_fees': 0.0,
            'upcoming_fees': 0.0,
        }
        
        # Calculate overdue and upcoming fees
        today = fields.Date.today()
        for fee_detail in self.fees_detail_ids:
            if fee_detail.state not in ('paid', 'cancel'):
                fee_amount = fee_detail.after_discount_amount or fee_detail.amount
                
                # Check due date from fees line if available
                due_date = None
                if hasattr(fee_detail, 'due_date') and fee_detail.due_date:
                    due_date = fee_detail.due_date
                elif fee_detail.fees_line_id and fee_detail.fees_line_id.due_date:
                    due_date = fee_detail.fees_line_id.due_date
                elif fee_detail.date:
                    # Use creation date + 30 days as default due date
                    due_date = fields.Date.add(fee_detail.date, days=30)
                
                if due_date:
                    if due_date < today:
                        summary['overdue_fees'] += fee_amount
                    elif due_date > today:
                        summary['upcoming_fees'] += fee_amount
        
        return summary

    def create_fee_payment_schedule(self, fees_term_id, start_date=None):
        """Create fee payment schedule for student based on fee terms.
        
        Args:
            fees_term_id (int): Fee terms ID
            start_date (date): Optional start date for schedule
            
        Returns:
            list: Created fee detail records
        """
        self.ensure_one()
        
        if not start_date:
            start_date = fields.Date.today()
        
        fees_term = self.env['op.fees.terms'].browse(fees_term_id)
        if not fees_term.exists():
            raise UserError(_("Invalid fee terms specified."))
        
        # Calculate total fees for the student's course
        if not self.course_detail_ids:
            raise UserError(
                _("Student '%s' has no course enrollment. "
                  "Please enroll student in a course first.") % self.name)
        
        latest_course = self.course_detail_ids[0]
        total_amount = fees_term.calculate_total_fees(
            self.id, latest_course.course_id.id)
        
        if total_amount <= 0:
            raise UserError(
                _("Cannot calculate fee amount for the specified course. "
                  "Please configure fee elements for the course."))
        
        # Generate payment schedule
        schedule = fees_term.get_payment_schedule(start_date, total_amount)
        created_records = []
        
        for payment in schedule:
            fee_detail_vals = {
                'student_id': self.id,
                'fees_line_id': payment['line_id'],
                'amount': payment['amount'],
                'date': start_date,
                'course_id': latest_course.course_id.id,
                'batch_id': latest_course.batch_id.id,
                'state': 'draft',
                'discount': payment.get('discount', 0.0)
            }
            
            # Add primary product from fee elements or use default
            if payment.get('elements'):
                element = self.env['op.fees.element'].search([
                    ('fees_terms_line_id', '=', payment['line_id'])
                ], limit=1)
                if element:
                    fee_detail_vals['product_id'] = element.product_id.id
            
            fee_detail = self.env['op.student.fees.details'].create(fee_detail_vals)
            created_records.append(fee_detail)
        
        return created_records

    def get_fee_analysis_data(self):
        """Get comprehensive fee analysis data for reporting.
        
        Returns:
            dict: Analysis data including payments, pending amounts, etc.
        """
        self.ensure_one()
        
        analysis = {
            'student_info': {
                'name': self.name,
                'student_id': self.student_id,
                'current_course': '',
                'current_batch': ''
            },
            'financial_summary': self.get_fees_summary(),
            'payment_history': [],
            'pending_payments': [],
            'overdue_payments': [],
            'fee_breakdown': {}
        }
        
        # Add current course/batch info
        if self.course_detail_ids:
            latest_course = self.course_detail_ids[0]
            analysis['student_info']['current_course'] = latest_course.course_id.name
            analysis['student_info']['current_batch'] = latest_course.batch_id.name
        
        # Analyze fee details
        today = fields.Date.today()
        for fee_detail in self.fees_detail_ids:
            fee_data = {
                'amount': fee_detail.amount,
                'after_discount': fee_detail.after_discount_amount,
                'date': fee_detail.date,
                'product': fee_detail.product_id.name,
                'state': fee_detail.state,
                'invoice_state': fee_detail.invoice_state,
                'discount': fee_detail.discount
            }
            
            if fee_detail.state in ('paid', 'invoice') and fee_detail.invoice_id:
                if fee_detail.invoice_id.payment_state == 'paid':
                    analysis['payment_history'].append(fee_data)
                else:
                    analysis['pending_payments'].append(fee_data)
            elif fee_detail.state not in ('cancel',):
                # Check if overdue
                due_date = getattr(fee_detail, 'due_date', None) or \
                          fields.Date.add(fee_detail.date, days=30)
                if due_date < today:
                    analysis['overdue_payments'].append(fee_data)
                else:
                    analysis['pending_payments'].append(fee_data)
            
            # Fee breakdown by product category
            category = fee_detail.product_id.categ_id.name
            if category not in analysis['fee_breakdown']:
                analysis['fee_breakdown'][category] = {
                    'total': 0.0,
                    'paid': 0.0,
                    'pending': 0.0
                }
            
            fee_amount = fee_detail.after_discount_amount or fee_detail.amount
            analysis['fee_breakdown'][category]['total'] += fee_amount
            
            if (fee_detail.state in ('paid', 'invoice') and 
                fee_detail.invoice_id and 
                fee_detail.invoice_id.payment_state == 'paid'):
                analysis['fee_breakdown'][category]['paid'] += fee_amount
            else:
                analysis['fee_breakdown'][category]['pending'] += fee_amount
        
        return analysis
