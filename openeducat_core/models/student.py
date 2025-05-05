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


class OpStudentCourse(models.Model):
    """Student Course Details model.

    This model manages the relationship between students and their courses,
    including batch information, roll numbers, and academic details.

    Attributes:
        student_id (int): Reference to the student
        course_id (int): Reference to the course
        batch_id (int): Reference to the batch
        roll_number (str): Student's roll number in the course
        subject_ids (list): List of subjects enrolled
        academic_years_id (int): Reference to academic year
        academic_term_id (int): Reference to academic term
        state (str): Current status of the course enrollment
    """

    _name = "op.student.course"
    _description = "Student Course Details"
    _inherit = "mail.thread"
    _rec_name = 'student_id'
    _order = 'student_id, course_id'

    student_id = fields.Many2one(
        comodel_name='op.student',
        string='Student',
        ondelete="cascade",
        tracking=True,
        help="Student enrolled in the course"
    )
    
    course_id = fields.Many2one(
        comodel_name='op.course',
        string='Course',
        required=True,
        tracking=True,
        help="Course in which student is enrolled"
    )
    
    batch_id = fields.Many2one(
        comodel_name='op.batch',
        string='Batch',
        tracking=True,
        help="Batch to which student belongs"
    )
    
    roll_number = fields.Char(
        string='Roll Number',
        tracking=True,
        help="Student's roll number in the course"
    )
    
    subject_ids = fields.Many2many(
        comodel_name='op.subject',
        string='Subjects',
        help="Subjects enrolled by the student"
    )
    
    academic_years_id = fields.Many2one(
        comodel_name='op.academic.year',
        string='Academic Year',
        help="Academic year of enrollment"
    )
    
    academic_term_id = fields.Many2one(
        comodel_name='op.academic.term',
        string='Terms',
        help="Academic term of enrollment"
    )
    
    state = fields.Selection(
        selection=[
            ('running', 'Running'),
            ('finished', 'Finished')
        ],
        string="Status",
        default="running",
        tracking=True,
        help="Current status of the course enrollment"
    )

    _sql_constraints = [
        ('unique_name_roll_number_id',
         'unique(roll_number,course_id,batch_id,student_id)',
         'Roll Number & Student must be unique per Batch!'),
        ('unique_name_roll_number_course_id',
         'unique(roll_number,course_id,batch_id)',
         'Roll Number must be unique per Batch!'),
        ('unique_name_roll_number_student_id',
         'unique(student_id,course_id,batch_id)',
         'Student must be unique per Batch!'),
    ]

    @api.model
    def get_import_templates(self):
        """Get the import template for student course details.

        Returns:
            List containing template information with label and template path.
        """
        return [{
            'label': _('Import Template for Student Course Details'),
            'template': '/openeducat_core/static/xls/op_student_course.xls'
        }]


class OpStudent(models.Model):
    """Student model.

    This model manages student information including personal details,
    academic records, and user account management.

    Attributes:
        first_name (str): Student's first name
        middle_name (str): Student's middle name
        last_name (str): Student's last name
        birth_date (date): Student's date of birth
        blood_group (str): Student's blood group
        gender (str): Student's gender
        nationality (int): Reference to student's nationality
        emergency_contact (int): Reference to emergency contact
        visa_info (str): Student's visa information
        id_number (str): Student's ID card number
        partner_id (int): Reference to partner record
        user_id (int): Reference to user account
        gr_no (str): Student's registration number
        category_id (int): Reference to student category
        course_detail_ids (list): List of course enrollments
        active (bool): Whether the student record is active
    """

    _name = "op.student"
    _description = "Student"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}
    _order = 'name'

    first_name = fields.Char(
        string='First Name',
        translate=True,
        tracking=True,
        help="Student's first name"
    )
    
    middle_name = fields.Char(
        string='Middle Name',
        translate=True,
        tracking=True,
        help="Student's middle name"
    )
    
    last_name = fields.Char(
        string='Last Name',
        translate=True,
        tracking=True,
        help="Student's last name"
    )
    
    birth_date = fields.Date(
        string='Birth Date',
        tracking=True,
        help="Student's date of birth"
    )
    
    blood_group = fields.Selection(
        selection=[
            ('A+', 'A+ve'),
            ('B+', 'B+ve'),
            ('O+', 'O+ve'),
            ('AB+', 'AB+ve'),
            ('A-', 'A-ve'),
            ('B-', 'B-ve'),
            ('O-', 'O-ve'),
            ('AB-', 'AB-ve')
        ],
        string='Blood Group',
        tracking=True,
        help="Student's blood group"
    )
    
    gender = fields.Selection(
        selection=[
            ('m', 'Male'),
            ('f', 'Female'),
            ('o', 'Other')
        ],
        string='Gender',
        required=True,
        default='m',
        tracking=True,
        help="Student's gender"
    )
    
    nationality = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        tracking=True,
        help="Student's nationality"
    )
    
    emergency_contact = fields.Many2one(
        comodel_name='res.partner',
        string='Emergency Contact',
        tracking=True,
        help="Student's emergency contact person"
    )
    
    visa_info = fields.Char(
        string='Visa Info',
        size=64,
        tracking=True,
        help="Student's visa information"
    )
    
    id_number = fields.Char(
        string='ID Card Number',
        size=64,
        tracking=True,
        help="Student's ID card number"
    )
    
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete="cascade",
        help="Associated partner record"
    )
    
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        ondelete="cascade",
        help="Associated user account"
    )
    
    gr_no = fields.Char(
        string="Registration Number",
        size=20,
        tracking=True,
        help="Student's registration number"
    )
    
    category_id = fields.Many2one(
        comodel_name='op.category',
        string='Category',
        tracking=True,
        help="Student's category"
    )
    
    course_detail_ids = fields.One2many(
        comodel_name='op.student.course',
        inverse_name='student_id',
        string='Course Details',
        tracking=True,
        help="Student's course enrollments"
    )
    
    active = fields.Boolean(
        default=True,
        help="If unchecked, the student will be hidden from the system"
    )

    _sql_constraints = [(
        'unique_gr_no',
        'unique(gr_no)',
        'Registration Number must be unique per student!'
    )]

    @api.onchange('first_name', 'middle_name', 'last_name')
    def _onchange_name(self):
        """Update the name field based on first, middle, and last names."""
        if not self.middle_name:
            self.name = str(self.first_name) + " " + str(self.last_name)
        else:
            self.name = str(self.first_name) + " " + str(self.middle_name) + " " + str(self.last_name)

    @api.constrains('birth_date')
    def _check_birthdate(self):
        """Validate that birth date is not in the future.

        Raises:
            ValidationError: If birth date is greater than current date.
        """
        for record in self:
            if record.birth_date and record.birth_date > fields.Date.today():
                raise ValidationError(_("Birth Date can't be greater than current date!"))

    @api.model
    def get_import_templates(self):
        """Get the import template for students.

        Returns:
            List containing template information with label and template path.
        """
        return [{
            'label': _('Import Template for Students'),
            'template': '/openeducat_core/static/xls/op_student.xls'
        }]

    def create_student_user(self):
        """Create a portal user account for the student.

        Creates a new user account with portal access rights and links it to the student.
        """
        user_group = self.env.ref("base.group_portal") or False
        users_res = self.env['res.users']
        for record in self:
            if not record.user_id:
                user_id = users_res.create({
                    'name': record.name,
                    'partner_id': record.partner_id.id,
                    'login': record.email,
                    'groups_id': user_group,
                    'is_student': True,
                    'tz': self._context.get('tz'),
                })
                record.user_id = user_id

    @api.constrains('first_name', 'last_name')
    def _check_names(self):
        """Validate that first name and last name are provided.

        Raises:
            ValidationError: If first name or last name is missing.
        """
        for record in self:
            if not record.first_name:
                raise ValidationError(_("First name is required!"))
            if not record.last_name:
                raise ValidationError(_("Last name is required!"))

    @api.constrains('email')
    def _check_email(self):
        """Validate that email is unique and properly formatted.

        Raises:
            ValidationError: If email is not unique or invalid.
        """
        for record in self:
            if record.email:
                duplicate = self.search([
                    ('email', '=', record.email),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_("Email must be unique!"))
