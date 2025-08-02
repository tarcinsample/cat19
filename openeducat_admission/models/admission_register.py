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

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpAdmissionRegister(models.Model):
    _name = "op.admission.register"
    _inherit = "mail.thread"
    _description = "Admission Register"
    _order = 'id DESC'

    name = fields.Char(
        'Name', required=True, readonly=True)
    start_date = fields.Date(
        'Start Date', required=True, readonly=True,
        default=fields.Date.today())
    end_date = fields.Date(
        'End Date', required=False, readonly=True,
        default=(fields.Date.today() + relativedelta(days=30)))
    course_id = fields.Many2one(
        'op.course', 'Course', readonly=True, tracking=True)
    min_count = fields.Integer(
        'Minimum No. of Admission', readonly=True)
    max_count = fields.Integer(
        'Maximum No. of Admission', readonly=True, default=30)
    product_id = fields.Many2one(
        'product.product', 'Course Fees',
        domain=[('type', '=', 'service')], tracking=True)
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
    minimum_age_criteria = fields.Integer('Minimum Required Age(Years)', default=3)
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
            ValidationError: If end date is before start date
        """
        for record in self:
            if not record.start_date:
                continue
                
            if record.end_date and record.start_date > record.end_date:
                raise ValidationError(_(
                    "End Date (%s) cannot be set before Start Date (%s).") % (
                    record.end_date, record.start_date))

    @api.constrains('min_count', 'max_count')
    def check_no_of_admission(self):
        """Validate admission count constraints.
        
        Raises:
            ValidationError: If admission counts are invalid
        """
        for record in self:
            if record.min_count <= 0 or record.max_count <= 0:
                raise ValidationError(_(
                    "Minimum (%s) and Maximum (%s) admission counts must be positive.") % (
                    record.min_count, record.max_count))
            if record.min_count > record.max_count:
                raise ValidationError(_(
                    "Minimum admission count (%s) cannot be greater than "
                    "Maximum admission count (%s).") % (
                    record.min_count, record.max_count))

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
        if not self.course_id and self.admission_base == 'course':
            raise ValidationError(_("Course must be selected for course-based admission."))
        if not self.program_id and self.admission_base == 'program':
            raise ValidationError(_("Program must be selected for program-based admission."))
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
        if self.admission_ids.filtered(lambda a: a.state in ['confirm', 'admission', 'done']):
            raise ValidationError(_(
                "Cannot cancel register with confirmed or enrolled applications."))
        self.state = 'cancel'

    def start_application(self):
        """Start application gathering phase."""
        self.ensure_one()
        if self.state != 'confirm':
            raise ValidationError(_("Register must be confirmed before starting applications."))
        self.state = 'application'

    def start_admission(self):
        """Start admission process phase."""
        self.ensure_one()
        if self.state != 'application':
            raise ValidationError(_("Must be in application phase before starting admissions."))
        self.state = 'admission'

    def close_register(self):
        """Close admission register and mark as completed."""
        self.ensure_one()
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
