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

from datetime import datetime
from typing import Dict, List, Any

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class OpAdmission(models.Model):
    """Student admission application management.
    
    This model manages the complete admission process from application 
    submission to student enrollment. It handles workflow states,
    validation, fee calculation, and student record creation.
    
    Workflow states:
    - draft: Initial application state
    - submit: Application submitted for review
    - confirm: Application confirmed by staff
    - admission: Admission approved
    - done: Student enrolled successfully
    - reject: Application rejected
    - pending: Application on hold
    - cancel: Application cancelled
    """
    _name = "op.admission"
    _inherit = ['mail.thread', 'mail.activity.mixin',
                'mail.tracking.duration.mixin']
    _rec_name = "application_number"
    _description = "Admission"
    _order = 'id DESC'

    name = fields.Char(
        'Name', required=True, translate=True)
    first_name = fields.Char(
        'First Name', required=True, translate=True)
    middle_name = fields.Char(
        'Middle Name', translate=True)
    last_name = fields.Char(
        'Last Name', required=True, translate=True)
    title = fields.Many2one(
        'res.partner.title', 'Title')
    application_number = fields.Char(
        'Application Number', size=16, copy=False,
        readonly=True, store=True)
    admission_date = fields.Date(
        'Admission Date', copy=False, tracking=True,
        help="Date when admission was confirmed")
    application_date = fields.Datetime(
        'Application Date', required=True, copy=False, tracking=True,
        default=lambda self: fields.Datetime.now(),
        help="Date when application was submitted")
    birth_date = fields.Date(
        'Birth Date', required=True)
    course_id = fields.Many2one(
        'op.course', 'Course', required=True, tracking=True, index=True,
        help="Course for which admission is being applied")
    batch_id = fields.Many2one(
        'op.batch', 'Batch', required=False, index=True, tracking=True,
        domain="[('course_id', '=', course_id), ('active', '=', True)]",
        help="Batch associated with the selected course")
    street = fields.Char(
        'Street', size=256)
    street2 = fields.Char(
        'Street2', size=256)
    phone = fields.Char(
        'Phone', size=16)
    mobile = fields.Char(
        'Mobile', size=16)
    email = fields.Char(
        'Email', size=256, required=True, tracking=True,
        help="Email address for communication")
    city = fields.Char('City', size=64)
    zip = fields.Char('Zip', size=8)
    state_id = fields.Many2one(
        'res.country.state', 'States', domain="[('country_id', '=', country_id)]")
    country_id = fields.Many2one(
        'res.country', 'Country')
    fees = fields.Float('Fees', digits='Product Price', default=0.0,
                      help="Total admission fees amount")
    image = fields.Image('image')
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted'),
         ('confirm', 'Confirmed'), ('admission', 'Admission Confirm'),
         ('reject', 'Rejected'), ('pending', 'Pending'),
         ('cancel', 'Cancelled'), ('done', 'Done')],
        'State', default='draft', tracking=True, index=True)
    due_date = fields.Date('Due Date')
    prev_institute_id = fields.Char('Previous Institute')
    prev_course_id = fields.Char('Previous Course')
    prev_result = fields.Char(
        'Previous Result', size=256)
    family_business = fields.Char(
        'Family Business', size=256)
    family_income = fields.Float(
        'Family Income')
    gender = fields.Selection(
        [('m', 'Male'), ('f', 'Female')],
        string='Gender',
        required=True)
    student_id = fields.Many2one(
        'op.student', 'Student', readonly=True, tracking=True,
        help="Student record created after enrollment")
    nbr = fields.Integer('No of Admission', readonly=True, default=0,
                       help="Admission sequence number")
    register_id = fields.Many2one(
        'op.admission.register', 'Admission Register', required=True, tracking=True,
        help="Admission register for this admission cycle")
    partner_id = fields.Many2one('res.partner', 'Partner')
    is_student = fields.Boolean('Is Already Student')
    fees_term_id = fields.Many2one('op.fees.terms', 'Fees Term')
    active = fields.Boolean(default=True)
    discount = fields.Float(string='Discount (%)',
                            digits='Discount', default=0.0)

    fees_start_date = fields.Date('Fees Start Date',
                                 help="Date from which fees payment starts")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    program_id = fields.Many2one('op.program', string="Program", tracking=True)
    course_ids = fields.Many2many('op.course', string='Courses',
                                  compute='_compute_course_ids')

    _sql_constraints = [
        ('unique_application_number',
         'unique(application_number)',
         'Application Number must be unique per Application!'),
    ]

    @api.depends('register_id')
    def _compute_course_ids(self):
        for data in self:
            if data.register_id:
                if data.register_id.admission_base == 'program':
                    course_list = []
                    for rec in data.register_id.admission_fees_line_ids:
                        course_list.append(rec.course_id.id) if rec.course_id.id not in course_list else None  # noqa
                    data.course_ids = [(6, 0, course_list)]
                else:
                    data.course_id = data.register_id.course_id.id
                    data.course_ids = [(6, 0, [data.register_id.course_id.id])]
            else:
                data.course_ids = [(6, 0, [])]

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_name(self):
        """Compute full name from first, middle, and last names.
        
        Handles None values gracefully and uses proper string formatting.
        """
        name_parts = []
        
        if self.first_name:
            name_parts.append(str(self.first_name).strip())
        if self.middle_name:
            name_parts.append(str(self.middle_name).strip())
        if self.last_name:
            name_parts.append(str(self.last_name).strip())
            
        self.name = ' '.join(name_parts) if name_parts else False

    @api.onchange('student_id', 'is_student')
    def onchange_student(self):
        """Update admission fields when existing student is selected.
        
        Safely copies student information to admission fields.
        """
        if self.is_student and self.student_id:
            sd = self.student_id
            self.title = sd.title and sd.title.id or False
            self.first_name = sd.first_name
            self.middle_name = sd.middle_name
            self.last_name = sd.last_name
            self.birth_date = sd.birth_date
            self.gender = sd.gender
            self.image = sd.image_1920 or False
            self.street = sd.street or False
            self.street2 = sd.street2 or False
            self.phone = sd.phone or False
            self.mobile = sd.mobile or False
            self.email = sd.email or False
            self.zip = sd.zip or False
            self.city = sd.city or False
            self.country_id = sd.country_id and sd.country_id.id or False
            self.state_id = sd.state_id and sd.state_id.id or False
            self.partner_id = sd.partner_id and sd.partner_id.id or False
        else:
            self.birth_date = False
            self.gender = False
            self.image = False
            self.street = False
            self.street2 = False
            self.phone = False
            self.mobile = False
            self.zip = False
            self.city = False
            self.country_id = False
            self.state_id = False
            self.partner_id = False

    @api.onchange('register_id')
    def onchange_register(self):
        """Update admission fields based on selected register.
        
        Sets course, program, fees, and company based on register configuration.
        """
        if self.register_id:
            if self.register_id.admission_base == 'course':
                if self.course_id and self.course_id.program_id:
                    self.program_id = self.course_id.program_id.id
                if self.register_id.product_id:
                    self.fees = self.register_id.product_id.lst_price
                if self.register_id.company_id:
                    self.company_id = self.register_id.company_id.id
            else:
                if self.register_id.program_id:
                    self.program_id = self.register_id.program_id.id

    @api.onchange('course_id')
    def onchange_course(self):
        """Update course-related fields when course is selected.
        
        Clears batch, updates program, calculates fees, and sets fees term.
        """
        self.batch_id = False
        term_id = False
        
        if self.course_id:
            # Set program from course
            if self.course_id.program_id:
                self.program_id = self.course_id.program_id.id
                
            # Calculate fees for program-based admission
            if self.register_id and self.register_id.admission_base == 'program':
                for rec in self.register_id.admission_fees_line_ids:
                    if rec.course_id and rec.course_id.id == self.course_id.id:
                        if rec.course_fees_product_id:
                            self.fees = rec.course_fees_product_id.lst_price
                        break
                        
            # Set fees term from course
            if self.course_id.fees_term_id:
                term_id = self.course_id.fees_term_id.id
                
        self.fees_term_id = term_id

    @api.constrains('register_id', 'application_date')
    def _check_admission_register(self):
        """Validate application date within admission register period.
        
        Raises:
            ValidationError: If application date is outside register period
        """
        for rec in self:
            if not rec.register_id:
                continue
            
            start_date = rec.register_id.start_date
            end_date = rec.register_id.end_date
            application_date = rec.application_date.date() if rec.application_date else False
            
            if not application_date:
                raise ValidationError(_("Application date is required."))
                
            if application_date < start_date or application_date > end_date:
                raise ValidationError(_(
                    "Application Date (%s) should be between Start Date (%s) "
                    "and End Date (%s) of Admission Register '%s'.") % (
                    application_date, start_date, end_date, rec.register_id.name))

    @api.constrains('birth_date', 'register_id')
    def _check_birthdate(self):
        """Validate birth date and age criteria.
        
        Raises:
            ValidationError: If birth date is invalid or age criteria not met
        """
        for record in self:
            if not record.birth_date:
                raise ValidationError(_("Birth date is required for admission."))
                
            today_date = fields.Date.today()
            
            # Check birth date not in future
            if record.birth_date > today_date:
                raise ValidationError(_(
                    "Birth Date (%s) cannot be greater than current date (%s).") % (
                    record.birth_date, today_date))
            
            # Check reasonable birth date (not too old)
            min_birth_date = today_date - relativedelta(years=100)
            if record.birth_date < min_birth_date:
                raise ValidationError(_(
                    "Birth date (%s) seems invalid. Please check the date.") % record.birth_date)
            
            # Check minimum age criteria if register has requirement
            if record.register_id and hasattr(record.register_id, 'minimum_age_criteria'):
                min_age = record.register_id.minimum_age_criteria or 0
                if min_age > 0:
                    age_years = relativedelta(today_date, record.birth_date).years
                    if age_years < min_age:
                        raise ValidationError(_(
                            "Not eligible for admission. Minimum required age is %s years. "
                            "Current age is %s years.") % (min_age, age_years))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate application number sequence.
        
        Ensures application number is generated with proper error handling.
        Validates required fields before creation.
        """
        for vals in vals_list:
            # Validate required fields
            if not vals.get('name') and vals.get('first_name') and vals.get('last_name'):
                # Auto-generate name if not provided
                name_parts = []
                if vals.get('first_name'):
                    name_parts.append(str(vals['first_name']).strip())
                if vals.get('middle_name'):
                    name_parts.append(str(vals['middle_name']).strip())
                if vals.get('last_name'):
                    name_parts.append(str(vals['last_name']).strip())
                vals['name'] = ' '.join(name_parts) if name_parts else 'New Admission'
            
            # Generate application number if not provided
            if not vals.get('application_number'):
                sequence = self.env['ir.sequence'].next_by_code('op.admission')
                if not sequence:
                    raise ValidationError(_(
                        "Unable to generate application number. "
                        "Please check admission sequence configuration."))
                vals['application_number'] = sequence
                
            # Set default application date if not provided
            if not vals.get('application_date'):
                vals['application_date'] = fields.Datetime.now()
                
            # Ensure company is set
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id
                
        return super(OpAdmission, self).create(vals_list)

    def submit_form(self):
        """Submit admission application for review.
        
        Validates required fields before submission.
        """
        self.ensure_one()
        
        # Validate required fields
        missing_fields = []
        if not self.name:
            missing_fields.append('Name')
        if not self.email:
            missing_fields.append('Email')
        if not self.birth_date:
            missing_fields.append('Birth Date')
        if not self.course_id:
            missing_fields.append('Course')
        if not self.register_id:
            missing_fields.append('Admission Register')
            
        if missing_fields:
            raise ValidationError(_(
                "The following fields are required to submit application: %s") % 
                ', '.join(missing_fields))
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValidationError(_("Please enter a valid email address."))
            
        self.state = 'submit'

    def admission_confirm(self):
        """Confirm admission application.
        
        Validates course and batch availability before confirmation.
        """
        self.ensure_one()
        
        # Validate required fields for confirmation
        if not self.course_id:
            raise ValidationError(_("Course must be selected before confirmation."))
            
        # Check if register allows confirmations
        if self.register_id.state not in ['application', 'admission']:
            raise ValidationError(_(
                "Cannot confirm admission. Register '%s' is not in application or admission phase.") % 
                self.register_id.name)
        
        # Check maximum admission count
        if self.register_id.max_count:
            confirmed_count = self.env['op.admission'].search_count([
                ('register_id', '=', self.register_id.id),
                ('state', 'in', ['admission', 'confirm', 'done'])
            ])
            if confirmed_count >= self.register_id.max_count:
                raise ValidationError(_(
                    "Cannot confirm admission. Maximum admission limit (%s) reached for register '%s'.") % 
                    (self.register_id.max_count, self.register_id.name))
        
        self.state = 'admission'

    def confirm_in_progress(self):
        """Set admission status to confirmed/in-progress.
        
        Validates admission criteria before confirming.
        """
        for record in self:
            # Validate state transition
            if record.state not in ['admission']:
                raise ValidationError(_(
                    "Cannot confirm admission from '%s' state. Must be in 'admission' state.") % 
                    record.state)
            
            # Check batch requirement for course-based admission
            if (record.register_id and 
                record.register_id.admission_base == 'course' and 
                not record.batch_id):
                raise ValidationError(_("Batch must be selected for course-based admission."))
                
            # Check if batch has capacity (if applicable)
            if record.batch_id and hasattr(record.batch_id, 'max_strength'):
                if record.batch_id.max_strength:
                    current_students = self.env['op.student.course'].search_count([
                        ('batch_id', '=', record.batch_id.id),
                        ('active', '=', True)
                    ])
                    if current_students >= record.batch_id.max_strength:
                        raise ValidationError(_(
                            "Cannot confirm admission. Batch '%s' has reached maximum capacity.") % 
                            record.batch_id.name)
            
            record.state = 'confirm'

    def get_student_vals(self):
        """Prepare student creation values from admission data.
        
        Creates user account if configuration parameter is enabled.
        Formats all student data including course details and fee information.
        
        Returns:
            dict: Dictionary containing student creation values
        """
        enable_create_student_user = self.env['ir.config_parameter'].get_param(
            'openeducat_admission.enable_create_student_user')
        for student in self:
            student_user = False
            if enable_create_student_user:
                student_user = self.env['res.users'].create({
                    'name': student.name,
                    'login': student.email if student.email else student.application_number,  # noqa
                    'image_1920': self.image or False,
                    'is_student': True,
                    'company_id': self.company_id.id,
                    'groups_id': [
                        (6, 0,
                         [self.env.ref('base.group_portal').id])]
                })
            details = {
                'name': student.name,
                'phone': student.phone,
                'mobile': student.mobile,
                'email': student.email,
                'street': student.street,
                'street2': student.street2,
                'city': student.city,
                'country_id':
                    student.country_id and student.country_id.id or False,
                'state_id': student.state_id and student.state_id.id or False,
                'image_1920': student.image,
                'zip': student.zip,
            }
            if enable_create_student_user:
                student_user.partner_id.write(details)
            details.update({
                'title': student.title and student.title.id or False,
                'first_name': student.first_name,
                'middle_name': student.middle_name,
                'last_name': student.last_name,
                'birth_date': student.birth_date,
                'gender': student.gender if student.gender else False,
                'image_1920': student.image or False,
                'course_detail_ids': [[0, False, {
                    'course_id':
                        student.course_id and student.course_id.id or False,
                    'batch_id':
                        student.batch_id and student.batch_id.id or False,
                    'academic_years_id':
                        student.register_id.academic_years_id and student.register_id.academic_years_id.id or False,
                    'academic_term_id':
                        student.register_id.academic_term_id and student.register_id.academic_term_id.id or False,
                    'fees_term_id': student.fees_term_id and student.fees_term_id.id or False,
                    'fees_start_date': student.fees_start_date or False,
                    'product_id': student.register_id.product_id and student.register_id.product_id.id or False,
                }]],
                'user_id': student_user.id if student_user else False,
                'company_id': self.company_id.id
            })
            return details

    def enroll_student(self):
        """Enroll student after admission confirmation.
        
        Creates student record, handles course enrollment, manages fee terms,
        and creates subject registration. Validates maximum admission count.
        
        Raises:
            ValidationError: If maximum admission count exceeded or invalid state
        """
        for record in self:
            # Validate state for enrollment
            if record.state not in ['confirm', 'admission']:
                raise ValidationError(_( 
                    "Cannot enroll student from '%s' state. Must be confirmed first.") % 
                    record.state)
            
            # Check maximum admission count
            max_count = record.register_id.max_count or 0
            if max_count > 0:
                total_admission = self.env['op.admission'].search_count(
                    [('register_id', '=', record.register_id.id),
                     ('state', '=', 'done')])
                if total_admission >= max_count:
                    raise ValidationError(_(
                        'Maximum admission limit (%s) reached for register "%s"') % (
                        max_count, record.register_id.name))
            
            # Validate required fields for enrollment
            if not record.course_id:
                raise ValidationError(_("Course must be selected before enrollment."))
            if not record.batch_id and record.register_id.admission_base == 'course':
                raise ValidationError(_("Batch must be selected for enrollment."))
            if not record.student_id:
                vals = record.get_student_vals()
                if vals:
                    record.student_id = student_id = self.env[
                        'op.student'].create(vals).id
                    record.partner_id = record.student_id.partner_id.id \
                        if record else False

            else:
                student_id = record.student_id.id
                record.student_id.write({
                    'course_detail_ids': [[0, False, {
                        'course_id':
                            record.course_id and record.course_id.id or False,
                        'batch_id':
                            record.batch_id and record.batch_id.id or False,
                        'academic_years_id':
                            record.register_id.academic_years_id and record.register_id.academic_years_id.id or False,
                        'academic_term_id':
                            record.register_id.academic_term_id and record.register_id.academic_term_id.id or False,
                        'fees_term_id': record.fees_term_id and record.fees_term_id.id or False,
                        'fees_start_date': record.fees_start_date or False,
                        'product_id': record.register_id.product_id and record.register_id.product_id.id or False,
                    }]],
                })
            if (record.fees_term_id and 
                record.fees_term_id.fees_terms in ['fixed_days', 'fixed_date']):
                val = []
                product_id = (record.register_id.product_id and 
                            record.register_id.product_id.id or False)
                for line in record.fees_term_id.line_ids:
                    no_days = line.due_days or 0
                    per_amount = line.value or 0
                    amount = (per_amount * (record.fees or 0)) / 100
                    dict_val = {
                        'fees_line_id': line.id,
                        'amount': amount,
                        'fees_factor': per_amount,
                        'product_id': product_id,
                        'discount': (record.discount or 
                                   (record.fees_term_id.discount if hasattr(record.fees_term_id, 'discount') else 0)),
                        'state': 'draft',
                        'course_id': record.course_id and record.course_id.id or False,
                        'batch_id': record.batch_id and record.batch_id.id or False,
                    }
                    if line.due_date:
                        date = line.due_date
                        dict_val.update({
                            'date': date
                        })
                    elif record.fees_start_date:
                        date = record.fees_start_date + relativedelta(
                            days=no_days)
                        dict_val.update({
                            'date': date,
                        })
                    else:
                        date_now = (datetime.today() + relativedelta(
                            days=no_days)).date()
                        dict_val.update({
                            'date': date_now,
                        })
                    val.append([0, False, dict_val])
                record.student_id.write({
                    'fees_detail_ids': val
                })
            record.write({
                'nbr': 1,
                'state': 'done',
                'admission_date': fields.Date.today(),
                'student_id': student_id,
                'is_student': True,
            })
            # Create subject registration if batch is available
            if record.batch_id:
                reg_id = self.env['op.subject.registration'].create({
                    'student_id': student_id,
                    'batch_id': record.batch_id.id,
                    'course_id': record.course_id.id,
                    'min_unit_load': record.course_id.min_unit_load or 0.0,
                    'max_unit_load': record.course_id.max_unit_load or 0.0,
                    'state': 'draft',
                })
                if hasattr(reg_id, 'get_subjects'):
                    reg_id.get_subjects()

    def confirm_rejected(self):
        """Reject the admission application.
        
        Can only be done from specific states.
        """
        self.ensure_one()
        if self.state not in ['submit', 'confirm', 'admission']:
            raise ValidationError(_(
                "Cannot reject admission from '%s' state.") % self.state)
        self.state = 'reject'

    def confirm_pending(self):
        """Put the admission application on pending status.
        
        Can be done from submit, confirm, or admission states.
        """
        self.ensure_one()
        if self.state not in ['submit', 'confirm', 'admission']:
            raise ValidationError(_(
                "Cannot set admission to pending from '%s' state.") % self.state)
        self.state = 'pending'

    def confirm_to_draft(self):
        """Reset admission application to draft state.
        
        Only allowed from specific states where modification is permitted.
        """
        self.ensure_one()
        if self.state in ['done']:
            raise ValidationError(_(
                "Cannot reset to draft from '%s' state. Student enrollment is complete.") % 
                self.state)
        self.state = 'draft'

    def confirm_cancel(self):
        """Cancel the admission application.
        
        Handles cleanup of related records including fees.
        """
        self.ensure_one()
        if self.state == 'done':
            raise ValidationError(_(
                "Cannot cancel admission that has already been completed. "
                "Please contact administrator."))
        
        # Cancel associated fees if student exists
        if self.is_student and self.student_id and self.student_id.fees_detail_ids:
            self.student_id.fees_detail_ids.write({'state': 'cancel'})
            
        self.state = 'cancel'

    def payment_process(self):
        self.state = 'fees_paid'

    def open_student(self):
        form_view = self.env.ref('openeducat_core.view_op_student_form')
        tree_view = self.env.ref('openeducat_core.view_op_student_tree')
        value = {
            'domain': str([('id', '=', self.student_id.id)]),
            'view_type': 'form',
            'view_mode': 'list, form',
            'res_model': 'op.student',
            'view_id': False,
            'views': [(form_view and form_view.id or False, 'form'),
                      (tree_view and tree_view.id or False, 'list')],
            'type': 'ir.actions.act_window',
            'res_id': self.student_id.id,
            'target': 'current',
            'nodestroy': True
        }
        self.state = 'done'
        return value

    def create_invoice(self):
        """ Create invoice for fee payment process of student """

        partner_id = self.env['res.partner'].create({'name': self.name})
        account_id = False
        product = self.register_id.product_id
        if product.id:
            account_id = product.property_account_income_id.id
        if not account_id:
            account_id = product.categ_id.property_account_income_categ_id.id
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". \
                   You may have to install a chart of account from Accounting \
                   app, settings menu.') % (product.name,))
        if self.fees <= 0.00:
            raise UserError(
                _('The value of the deposit amount must be positive.'))
        amount = self.fees
        name = product.name
        invoice = self.env['account.invoice'].create({
            'name': self.name,
            'origin': self.application_number,
            'move_type': 'out_invoice',
            'reference': False,
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': self.application_number,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.register_id.product_id.uom_id.id,
                'product_id': product.id,
            })],
        })
        invoice.compute_taxes()
        form_view = self.env.ref('account.invoice_form')
        tree_view = self.env.ref('account.invoice_tree')
        value = {
            'domain': str([('id', '=', invoice.id)]),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': False,
            'views': [(form_view and form_view.id or False, 'form'),
                      (tree_view and tree_view.id or False, 'list')],
            'type': 'ir.actions.act_window',
            'res_id': invoice.id,
            'target': 'current',
            'nodestroy': True
        }
        self.partner_id = partner_id
        self.state = 'payment_process'
        return value

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Admission'),
            'template': '/openeducat_admission/static/xls/op_admission.xls'
        }]


class OpStudentCourseInherit(models.Model):
    _inherit = "op.student.course"

    product_id = fields.Many2one(
        'product.product', 'Course Fees',
        domain=[('type', '=', 'service')], tracking=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_create_student_user = fields.Boolean(
        config_parameter='openeducat_admission.enable_create_student_user',
        string='Create Student User')
