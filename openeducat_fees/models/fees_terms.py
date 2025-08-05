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

from functools import lru_cache

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError


class OpFeesTermsLine(models.Model):
    """Model for managing individual fee term payment schedules.
    
    This model handles the breakdown of fee payments with due dates,
    percentages, and associated fee elements for each payment term.
    """
    _name = "op.fees.terms.line"
    _rec_name = "display_name"
    _description = "Fees Details Line"
    _order = "due_days, due_date"

    due_days = fields.Integer(
        'Due Days',
        help="Number of days for payment due calculation")
    due_date = fields.Date(
        'Due Date',
        help="Specific due date for payment")
    value = fields.Float(
        'Value (%)', required=True,
        help="Percentage of total fees due on this date")
    display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name showing due date and percentage")
    fees_element_line = fields.One2many(
        "op.fees.element", "fees_terms_line_id",
        string="Fees Elements",
        help="Individual fee elements for this term line")
    fees_id = fields.Many2one(
        'op.fees.terms', 'Fees Term',
        required=True, ondelete='cascade',
        help="Parent fees term")
    element_count = fields.Integer(
        'Element Count',
        compute='_compute_element_count',
        help="Number of fee elements in this line")

    _sql_constraints = [
        ('value_range',
         'CHECK (value >= 0 AND value <= 100)',
         'Percentage value must be between 0 and 100'),
        ('due_days_positive',
         'CHECK (due_days IS NULL OR due_days >= 0)',
         'Due days must be positive or null')
    ]

    @api.depends('due_days', 'due_date', 'value')
    def _compute_display_name(self):
        """Compute display name for the fee term line."""
        for line in self:
            if line.due_date:
                name = f"Due: {line.due_date}"
            elif line.due_days is not None:
                name = f"Due: {line.due_days} days"
            else:
                name = "Payment Term"
            
            if line.value:
                name += f" ({line.value}%)"
            line.display_name = name

    @api.depends('fees_element_line')
    def _compute_element_count(self):
        """Compute number of fee elements."""
        for line in self:
            line.element_count = len(line.fees_element_line)

    @api.constrains('value')
    def _check_value_range(self):
        """Validate percentage value range."""
        for line in self:
            if line.value < 0 or line.value > 100:
                raise ValidationError(
                    _("Percentage value must be between 0 and 100. "
                      "Current value: %s") % line.value
                )

    @api.constrains('due_days', 'due_date')
    def _check_due_date_consistency(self):
        """Validate due date consistency."""
        for line in self:
            if not line.due_days and not line.due_date:
                raise ValidationError(
                    _("Either due days or due date must be specified.")
                )
            if line.due_days and line.due_date:
                raise ValidationError(
                    _("Cannot specify both due days and due date. "
                      "Please use only one method.")
                )

    def calculate_due_date(self, start_date):
        """Calculate actual due date based on start date.
        
        Args:
            start_date (date): Fee calculation start date
            
        Returns:
            date: Calculated due date
        """
        self.ensure_one()
        if self.due_date:
            return self.due_date
        elif self.due_days is not None:
            return fields.Date.add(start_date, days=self.due_days)
        return start_date

    def get_fee_breakdown(self, total_amount):
        """Get fee breakdown for this term line.
        
        Args:
            total_amount (float): Total fee amount
            
        Returns:
            dict: Breakdown of fees by element
        """
        self.ensure_one()
        line_amount = (total_amount * self.value) / 100
        
        breakdown = {
            'line_total': line_amount,
            'percentage': self.value,
            'elements': []
        }
        
        for element in self.fees_element_line:
            element_amount = (line_amount * element.value) / 100
            breakdown['elements'].append({
                'product': element.product_id.name,
                'percentage': element.value,
                'amount': element_amount
            })
        
        return breakdown


class OpFeesTerms(models.Model):
    """Model for managing fee payment terms and schedules.
    
    This model handles the configuration of fee payment terms including
    installment schedules, due dates, discounts, and validation rules.
    """
    _name = "op.fees.terms"
    _inherit = "mail.thread"
    _description = "Fees Terms For Course"
    _order = "name, code"

    name = fields.Char(
        'Name', required=True,
        tracking=True,
        help="Name of the fee term")
    active = fields.Boolean(
        'Active', default=True,
        tracking=True,
        help="Set to False to hide the fee term")
    fees_terms = fields.Selection([
        ('fixed_days', 'Fixed Fees of Days'),
        ('fixed_date', 'Fixed Fees of Dates')
    ], string='Term Type', default='fixed_days',
        required=True, tracking=True,
        help="Type of fee term calculation")
    code = fields.Char(
        'Code', required=True,
        tracking=True,
        help="Unique code for the fee term")
    note = fields.Text(
        'Description',
        help="Additional description for the fee term")
    company_id = fields.Many2one(
        'res.company', 'Company',
        required=True, tracking=True,
        default=lambda s: s.env.user.company_id,
        help="Company for this fee term")
    no_days = fields.Integer(
        'No of Days',
        help="Number of days for fee calculation")
    day_type = fields.Selection([
        ('before', 'Before'),
        ('after', 'After')
    ], 'Type',
        help="Whether days are before or after start date")
    line_ids = fields.One2many(
        'op.fees.terms.line', 'fees_id',
        string='Payment Terms',
        help="Payment term lines with due dates and percentages")
    discount = fields.Float(
        string='Discount (%)',
        digits='Discount', default=0.0,
        tracking=True,
        help="Default discount percentage for this term")
    total_percentage = fields.Float(
        'Total Percentage',
        compute='_compute_total_percentage',
        help="Sum of all line percentages")
    line_count = fields.Integer(
        'Payment Lines',
        compute='_compute_line_count',
        help="Number of payment term lines")
    is_valid = fields.Boolean(
        'Valid Term',
        compute='_compute_validity',
        help="True if term configuration is valid")
    display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        help="Display name with code and type info")

    _sql_constraints = [
        ('unique_code',
         'unique(code)', 'Fee term code must be unique.'),
        ('discount_range',
         'CHECK (discount >= 0 AND discount <= 100)',
         'Discount must be between 0 and 100 percent'),
        ('no_days_positive',
         'CHECK (no_days IS NULL OR no_days >= 0)',
         'Number of days must be positive or null')
    ]

    @api.depends('line_ids.value')
    def _compute_total_percentage(self):
        """Compute total percentage from all lines."""
        for term in self:
            term.total_percentage = sum(line.value for line in term.line_ids)

    @api.depends('line_ids')
    def _compute_line_count(self):
        """Compute number of payment lines."""
        for term in self:
            term.line_count = len(term.line_ids)

    @api.depends('total_percentage', 'line_ids')
    def _compute_validity(self):
        """Compute if the fee term is valid."""
        for term in self:
            term.is_valid = (
                len(term.line_ids) > 0 and
                abs(term.total_percentage - 100.0) < 0.01
            )

    @api.constrains("line_ids")
    def terms_validation(self):
        """Validate fee terms configuration."""
        for term in self:
            if not term.line_ids:
                raise ValidationError(
                    _("Fee term '%s' must have at least one payment line.")
                    % term.name
                )
            
            total = sum(line.value for line in term.line_ids)
            if abs(total - 100.0) > 0.01:
                raise ValidationError(
                    _("Fee term '%s' payment percentages must sum to 100%%. "
                      "Current total: %.2f%%")
                    % (term.name, total)
                )

    @api.constrains('code')
    def _check_code_format(self):
        """Validate code format."""
        for term in self:
            if term.code and not term.code.replace('_', '').replace('-', '').isalnum():
                raise ValidationError(
                    _("Fee term code '%s' must contain only letters, numbers, "
                      "hyphens, and underscores.") % term.code
                )

    def _compute_display_name(self):
        """Compute display name for fee term with code and type info."""
        for term in self:
            name = f"{term.name} [{term.code}]"
            if term.fees_terms:
                term_type = dict(term._fields['fees_terms'].selection)[term.fees_terms]
                name += f" - {term_type}"
            if not term.is_valid:
                name += " (Invalid)"
            term.display_name = name

    def get_payment_schedule(self, start_date, total_amount):
        """Generate payment schedule for given start date and amount.
        
        Args:
            start_date (date): Fee calculation start date
            total_amount (float): Total fee amount
            
        Returns:
            list: Payment schedule with due dates and amounts
        """
        self.ensure_one()
        if not self.is_valid:
            raise ValidationError(
                _("Cannot generate payment schedule for invalid fee term '%s'")
                % self.name
            )
        
        schedule = []
        for line in self.line_ids.sorted('due_days'):
            due_date = line.calculate_due_date(start_date)
            line_amount = (total_amount * line.value) / 100
            
            # Apply discount if applicable
            if self.discount:
                discount_amount = (line_amount * self.discount) / 100
                line_amount -= discount_amount
            
            schedule.append({
                'line_id': line.id,
                'due_date': due_date,
                'amount': line_amount,
                'percentage': line.value,
                'discount': self.discount,
                'elements': line.fees_element_line.mapped('product_id.name')
            })
        
        return schedule

    @api.model
    def _get_cached_fee_calculation(self, term_id, student_id, course_id):
        """Cached helper method for fee calculation.
        
        Args:
            term_id (int): Fee term ID
            student_id (int): Student ID  
            course_id (int): Course ID
            
        Returns:
            float: Total calculated fee amount
        """
        # This creates a cache based on the database state
        term = self.browse(term_id)
        course = self.env['op.course'].search([('id', '=', course_id)], limit=1)
        total_amount = 0.0
        
        for line in term.line_ids:
            for element in line.fees_element_line:
                if element.course_id and element.course_id.id != course_id:
                    continue
                    
                # Calculate element amount
                if element.amount_type == 'fixed':
                    element_amount = element.amount
                else:  # percentage
                    base_amount = course.fees_amount if course else element.amount
                    element_amount = base_amount * element.percentage / 100.0
                
                # Apply line percentage
                line_amount = element_amount * line.value / 100.0
                total_amount += line_amount
                
        return total_amount

    def calculate_total_fees(self, student_id, course_id):
        """Calculate total fees for a student and course with caching.
        
        Args:
            student_id (int): Student ID
            course_id (int): Course ID
            
        Returns:
            float: Total calculated fee amount
        """
        self.ensure_one()
        
        # Use cached calculation if available
        cache_key = f"fee_calc_{self.id}_{student_id}_{course_id}"
        cached_result = self.env.registry.get(cache_key)
        
        if cached_result is not None:
            return cached_result
            
        # Calculate and cache result
        total_amount = self._get_cached_fee_calculation(self.id, student_id, course_id)
        
        # Cache result for 1 hour (3600 seconds)
        self.env.registry[cache_key] = total_amount
        
        return total_amount

    @api.model
    def get_active_terms(self, company_id=None):
        """Get all active fee terms for a company.
        
        Args:
            company_id (int): Company ID (None for current user's company)
            
        Returns:
            recordset: Active fee terms
        """
        domain = [('active', '=', True)]
        if company_id:
            domain.append(('company_id', '=', company_id))
        else:
            domain.append(('company_id', '=', self.env.user.company_id.id))
        
        return self.search(domain)

    def action_validate_terms(self):
        """Action to validate fee terms configuration."""
        self.ensure_one()
        try:
            self.terms_validation()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Validation Successful'),
                    'message': _('Fee term configuration is valid.'),
                    'type': 'success',
                }
            }
        except ValidationError as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Validation Failed'),
                    'message': str(e),
                    'type': 'danger',
                }
            }


class OpStudentCourseInherit(models.Model):
    """Extended student course model with fee term integration.
    
    This model adds fee term configuration to student course enrollments
    with proper validation and tracking.
    """
    _inherit = "op.student.course"

    fees_term_id = fields.Many2one(
        'op.fees.terms', 'Fees Term',
        domain="[('active', '=', True)]",
        help="Fee payment term for this course enrollment")
    fees_start_date = fields.Date(
        'Fees Start Date',
        help="Date from which fee calculation starts")
    total_fees = fields.Monetary(
        'Total Fees',
        compute='_compute_total_fees',
        store=True,
        currency_field='currency_id',
        help="Total calculated fees for this course")
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        related='fees_term_id.company_id.currency_id',
        readonly=True,
        help="Currency for fee calculations")

    @api.depends('fees_term_id', 'course_id', 'student_id')
    def _compute_total_fees(self):
        """Compute total fees based on fee term and course."""
        for record in self:
            if record.fees_term_id and record.course_id:
                record.total_fees = record.fees_term_id.calculate_total_fees(
                    record.student_id.id, record.course_id.id
                )
            else:
                record.total_fees = 0.0

    @api.onchange('course_id')
    def _onchange_course_id(self):
        """Set default fee term when course changes."""
        if self.course_id and self.course_id.fees_term_id:
            self.fees_term_id = self.course_id.fees_term_id.id
            if not self.fees_start_date:
                self.fees_start_date = fields.Date.today()

    @api.constrains('fees_term_id', 'fees_start_date')
    def _check_fees_configuration(self):
        """Validate fee configuration."""
        for record in self:
            if record.fees_term_id and not record.fees_start_date:
                raise ValidationError(
                    _("Fees start date is required when fee term is set.")
                )