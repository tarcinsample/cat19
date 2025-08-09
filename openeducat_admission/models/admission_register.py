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

from typing import Dict, List, Any

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpAdmissionRegister(models.Model):
    """Admission register for managing admission cycles.
    
    This model manages admission registration periods, defines course offerings,
    sets admission criteria, and tracks application progress. It serves as the
    master configuration for each admission cycle.
    
    Workflow states:
    - draft: Register being configured
    - confirm: Register confirmed and ready
    - application: Application gathering phase
    - admission: Admission processing phase  
    - done: Register closed
    - cancel: Register cancelled
    """
    _name = "op.admission.register"
    _inherit = "mail.thread"
    _description = "Admission Register"
    _order = 'id DESC'

    name = fields.Char(
        'Name', required=True, readonly=True, index=True,
        help="Name of the admission register")
    start_date = fields.Date(
        'Start Date', required=True, readonly=True,
        default=fields.Date.today())
    end_date = fields.Date(
        'End Date', required=True, readonly=True,
        default=(fields.Date.today() + relativedelta(days=30)),
        help="Last date for application submission")
    course_id = fields.Many2one(
        'op.course', 'Course', readonly=True, tracking=True)
    min_count = fields.Integer(
        'Minimum No. of Admission', readonly=True, default=1,
        help="Minimum number of admissions required")
    max_count = fields.Integer(
        'Maximum No. of Admission', readonly=True, default=30,
        help="Maximum number of admissions allowed")
    product_id = fields.Many2one(
        'product.product', 'Course Fees',
        domain=[('type', '=', 'service')], tracking=True,
        help="Product used for fees calculation")
    admission_ids = fields.One2many(
        'op.admission', 'register_id', 'Admissions')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),
         ('cancel', 'Cancelled'), ('application', 'Application Gathering'),
         ('admission', 'Admission Process'), ('done', 'Done')],
        'Status', default='draft', tracking=True)
    active = fields.Boolean(default=True)

    academic_years_id = \
        fields.Many2one('op.academic.year',
                        'Academic Year', readonly=True,
                        tracking=True)
    academic_term_id = fields.Many2one('op.academic.term',
                                       'Terms', readonly=True,
                                       tracking=True)
    minimum_age_criteria = fields.Integer('Minimum Required Age(Years)', default=3,
                                           help="Minimum age requirement for admission")
    application_count = fields.Integer(string="Total Applications",
                                       compute="_compute_calculate_record_application",
                                       help="Total number of applications for this register")
    is_favorite = fields.Boolean(string="Is Favorite", default=False,
                                help="Mark this register as favorite for quick access")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id,
                                 help="Company this admission register belongs to")
    draft_count = fields.Integer(compute="_compute_counts", string="Draft Applications",
                                help="Number of applications in draft state")
    confirm_count = fields.Integer(compute="_compute_counts", string="Confirmed Applications", 
                                  help="Number of confirmed applications")
    done_count = fields.Integer(compute="_compute_counts", string="Enrolled Students",
                               help="Number of students successfully enrolled")
    online_count = fields.Integer(compute='_compute_application_counts', string="Online Applications",
                                 help="Number of online applications")
    admission_base = fields.Selection([('program', 'Program'), ('course', 'Course')],
                                      default='course')
    admission_fees_line_ids = fields.One2many('op.admission.fees.line', 'register_id',
                                              string='Admission Fees Configuration')

    @api.onchange('admission_base')
    def onchange_admission_base(self):
        if self.admission_base:
            if self.admission_base == 'program':
                self.course_id = None
                self.product_id = None
            else:
                self.program_id = None
                self.admission_fees_line_ids = None

    program_id = fields.Many2one('op.program', string="Program", tracking=True)

    @api.depends('admission_ids.state')
    def _compute_counts(self):
        """Compute application counts by state.
        
        Efficiently counts applications in different states.
        """
        for record in self:
            admission_states = record.admission_ids.mapped('state')
            record.draft_count = admission_states.count('draft')
            record.confirm_count = admission_states.count('confirm')
            record.done_count = admission_states.count('done')

    @api.depends('admission_ids.state')
    def _compute_application_counts(self):
        """Compute online application counts.
        
        Efficiently counts online applications.
        """
        for record in self:
            admission_states = record.admission_ids.mapped('state')
            record.online_count = admission_states.count('online')

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        """Validate admission register date constraints.
        
        Raises:
            ValidationError: If end date is before start date or dates are invalid
        """
        for record in self:
            if not record.start_date:
                raise ValidationError(_("Start date is required for admission register."))
            if not record.end_date:
                raise ValidationError(_("End date is required for admission register."))
                
            if record.start_date > record.end_date:
                raise ValidationError(_(
                    "End Date (%s) cannot be set before Start Date (%s).") % (
                    record.end_date, record.start_date))
                    
            # Check if start date is too far in the past (more than 1 year)
            today = fields.Date.today()
            max_past_date = today - relativedelta(years=1)
            if record.start_date < max_past_date:
                raise ValidationError(_(
                    "Start date (%s) cannot be more than 1 year in the past.") % 
                    record.start_date)
                    
            # Check if end date is too far in the future (more than 2 years)
            max_future_date = today + relativedelta(years=2)
            if record.end_date > max_future_date:
                raise ValidationError(_(
                    "End date (%s) cannot be more than 2 years in the future.") % 
                    record.end_date)

    @api.constrains('min_count', 'max_count')
    def check_no_of_admission(self):
        """Validate admission count constraints.
        
        Raises:
            ValidationError: If admission counts are invalid
        """
        for record in self:
            min_count = record.min_count or 0
            max_count = record.max_count or 0
            
            if min_count < 0 or max_count <= 0:
                raise ValidationError(_(
                    "Minimum admission count (%s) cannot be negative and "
                    "Maximum admission count (%s) must be positive.") % (
                    min_count, max_count))
                    
            if min_count > max_count:
                raise ValidationError(_(
                    "Minimum admission count (%s) cannot be greater than "
                    "Maximum admission count (%s).") % (
                    min_count, max_count))
                    
            # Check reasonable limits
            if max_count > 10000:
                raise ValidationError(_(
                    "Maximum admission count (%s) seems unreasonably high. "
                    "Please check the value.") % max_count)

    def open_student_application(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "op.admission",
            "domain": [("register_id", "=", self.id)],
            "name": "Applications",
            "view_mode": "list,form",
        }

    @api.depends('admission_ids')
    def _compute_calculate_record_application(self):
        """Compute total application count.
        
        Efficiently counts total applications for this register.
        """
        for record in self:
            record.application_count = len(record.admission_ids)

    def confirm_register(self):
        """Confirm admission register and make it active for applications.
        
        Validates required fields before confirmation.
        """
        self.ensure_one()
        
        # Validate state
        if self.state != 'draft':
            raise ValidationError(_(
                "Cannot confirm register from '%s' state. Must be in 'draft' state.") % 
                self.state)
        
        # Validate required fields based on admission base
        if self.admission_base == 'course':
            if not self.course_id:
                raise ValidationError(_("Course must be selected for course-based admission."))
            if not self.product_id:
                raise ValidationError(_("Course fees product must be selected."))
        elif self.admission_base == 'program':
            if not self.program_id:
                raise ValidationError(_("Program must be selected for program-based admission."))
            if not self.admission_fees_line_ids:
                raise ValidationError(_(
                    "At least one course fee configuration is required for program-based admission."))
        
        # Validate academic year and dates
        if not self.academic_years_id:
            raise ValidationError(_("Academic year must be selected."))
            
        # Check if dates fall within academic year
        if (self.academic_years_id.start_date and self.start_date < self.academic_years_id.start_date) or \
           (self.academic_years_id.end_date and self.end_date > self.academic_years_id.end_date):
            raise ValidationError(_(
                "Admission register dates must fall within the selected academic year period."))
        
        self.state = 'confirm'

    def set_to_draft(self):
        """Reset admission register to draft state for editing."""
        self.ensure_one()
        self.state = 'draft'

    def cancel_register(self):
        """Cancel admission register.
        
        Validates that no confirmed applications exist.
        """
        self.ensure_one()
        
        # Check for applications that prevent cancellation
        blocking_states = ['confirm', 'admission', 'done']
        blocking_admissions = self.admission_ids.filtered(lambda a: a.state in blocking_states)
        
        if blocking_admissions:
            raise ValidationError(_(
                "Cannot cancel register with %s applications in confirmed, admission, or enrolled states. "
                "Please handle these applications first.") % len(blocking_admissions))
        
        # Check if register is already closed
        if self.state == 'done':
            raise ValidationError(_(
                "Cannot cancel a completed admission register."))
        
        self.state = 'cancel'

    def start_application(self):
        """Start application gathering phase.
        
        Validates register is confirmed and dates are appropriate.
        """
        self.ensure_one()
        
        if self.state != 'confirm':
            raise ValidationError(_(
                "Register must be confirmed before starting applications. Current state: %s") % 
                self.state)
        
        # Check if current date is within application period
        today = fields.Date.today()
        if today < self.start_date:
            raise ValidationError(_(
                "Cannot start applications before the start date (%s).") % self.start_date)
        if today > self.end_date:
            raise ValidationError(_(
                "Cannot start applications after the end date (%s).") % self.end_date)
        
        self.state = 'application'

    def start_admission(self):
        """Start admission process phase.
        
        Validates minimum application requirements are met.
        """
        self.ensure_one()
        
        if self.state != 'application':
            raise ValidationError(_(
                "Must be in application phase before starting admissions. Current state: %s") % 
                self.state)
        
        # Check if minimum applications received
        submitted_count = len(self.admission_ids.filtered(lambda a: a.state in ['submit', 'confirm', 'admission', 'done']))
        if submitted_count < self.min_count:
            raise ValidationError(_(
                "Cannot start admission process. Minimum %s applications required, only %s received.") % 
                (self.min_count, submitted_count))
        
        self.state = 'admission'

    def close_register(self):
        """Close admission register and mark as completed.
        
        Validates that admission process can be completed.
        """
        self.ensure_one()
        
        if self.state not in ['admission', 'application']:
            raise ValidationError(_(
                "Can only close register from admission or application phase. Current state: %s") % 
                self.state)
        
        # Generate summary statistics
        total_applications = len(self.admission_ids)
        enrolled_count = len(self.admission_ids.filtered(lambda a: a.state == 'done'))
        
        # Log completion summary
        self.message_post(
            body=_(
                "Admission register closed successfully.<br/>"
                "Total Applications: %s<br/>"
                "Successfully Enrolled: %s<br/>"
                "Enrollment Rate: %.1f%%") % (
                total_applications, 
                enrolled_count,
                (enrolled_count / total_applications * 100) if total_applications > 0 else 0
            )
        )
        
        self.state = 'done'

    def action_open_draft_courses(self):
        return {
            'name': 'Draft Admissions',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.admission',
            'domain': [
                ('id', 'in', self.admission_ids.ids),
                ('state', '=', 'draft'),
            ],
            'target': 'current',
        }

    def action_open_confirmed_courses(self):
        return {
            'name': 'Confirmed Courses',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.admission',
            'domain': [('id', 'in', self.admission_ids.ids), ('state', '=', 'confirm')],
            'target': 'current',
        }

    def action_open_enrolled_courses(self):
        return {
            'name': 'Enrolled Courses',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.admission',
            'domain': [('id', 'in', self.admission_ids.ids), ('state', '=', 'done')],
            'target': 'current',
        }

    def action_open_online_courses(self):
        return {
            'name': 'Enrolled Courses',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.admission',
            'domain': [('id', 'in', self.admission_ids.ids), ('state', '=', 'online')],
            'target': 'current',
        }


class AdmissionRegisterFeesLine(models.Model):
    _name = 'op.admission.fees.line'
    _description = "Admission Fees Line"

    course_id = fields.Many2one('op.course', string="Course", required=True)
    course_fees_product_id = fields.Many2one('product.product', string="Course Fees")
    register_id = fields.Many2one('op.admission.register', string="Admission Register")
