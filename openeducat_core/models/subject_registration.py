# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

###########################################################################
#
#    OpenEduCat Inc.
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
###########################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpSubjectRegistration(models.Model):
    """Subject Registration model for OpenEduCat.

    This model manages the registration of subjects for students,
    including both compulsory and elective subjects, with workflow states
    and unit load management.

    The registration process follows these states:
    - Draft: Initial state when registration is being prepared
    - Submitted: Registration has been submitted for approval
    - Approved: Registration has been approved and subjects are assigned
    - Rejected: Registration has been rejected

    Attributes:
        name (str): Registration sequence number
        student_id (int): Reference to the student
        course_id (int): Reference to the course
        batch_id (int): Reference to the batch
        compulsory_subject_ids (list): List of compulsory subjects
        elective_subject_ids (list): List of elective subjects
        state (str): Current state of registration
        max_unit_load (float): Maximum allowed unit load
        min_unit_load (float): Minimum required unit load
        is_read (bool): Whether the registration has been read
        company_id (int): Reference to the company
    """

    _name = "op.subject.registration"
    _description = "OpenEduCat Subject Registration"
    _inherit = ["mail.thread"]
    _order = 'name desc'

    name = fields.Char(
        string='Name',
        readonly=True,
        default='New',
        tracking=True,
        help="Registration sequence number"
    )
    
    student_id = fields.Many2one(
        comodel_name='op.student',
        string='Student',
        tracking=True,
        help="Student registering for subjects"
    )
    
    course_id = fields.Many2one(
        comodel_name='op.course',
        string='Course',
        required=True,
        tracking=True,
        help="Course for which subjects are being registered"
    )
    
    batch_id = fields.Many2one(
        comodel_name='op.batch',
        string='Batch',
        tracking=True,
        help="Batch to which student belongs"
    )
    
    compulsory_subject_ids = fields.Many2many(
        comodel_name='op.subject',
        relation='subject_compulsory_rel',
        column1='register_id',
        column2='subject_id',
        string="Compulsory Subjects",
        readonly=True,
        help="Compulsory subjects for the course"
    )
    
    elective_subject_ids = fields.Many2many(
        comodel_name='op.subject',
        string="Elective Subjects",
        help="Elective subjects chosen by the student"
    )
    
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        string='State',
        default='draft',
        copy=False,
        tracking=True,
        help="Current state of the registration"
    )
    
    max_unit_load = fields.Float(
        string='Maximum Unit Load',
        tracking=True,
        help="Maximum allowed unit load for the registration"
    )
    
    min_unit_load = fields.Float(
        string='Minimum Unit Load',
        tracking=True,
        help="Minimum required unit load for the registration"
    )
    
    is_read = fields.Boolean(
        string="Read?",
        default=False,
        help="Indicates if the registration has been read"
    )
    
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        help="Company to which the registration belongs"
    )

    def action_reset_draft(self):
        """Reset the registration state to draft.
        
        This method allows reverting a registration back to draft state
        for further modifications.
        """
        self.state = 'draft'

    def action_reject(self):
        """Reject the subject registration.
        
        This method marks the registration as rejected, indicating that
        the subject selection was not approved.
        """
        self.state = 'rejected'

    def action_approve(self):
        """Approve the subject registration and update student's course subjects.

        This method:
        1. Collects all selected subjects (compulsory and elective)
        2. Finds the student's course record
        3. Updates the course with the selected subjects
        4. Changes the registration state to approved

        Raises:
            ValidationError: If the student's course is not found.
        """
        for record in self:
            subject_ids = []
            for sub in record.compulsory_subject_ids:
                subject_ids.append(sub.id)
            for sub in record.elective_subject_ids:
                subject_ids.append(sub.id)
            
            course_id = self.env['op.student.course'].search([
                ('student_id', '=', record.student_id.id),
                ('course_id', '=', record.course_id.id)
            ], limit=1)
            
            if course_id:
                course_id.write({
                    'subject_ids': [[6, 0, list(set(subject_ids))]]
                })
                record.state = 'approved'
            else:
                raise ValidationError(_("Course not found on student's admission!"))

    def action_submitted(self):
        """Submit the subject registration for approval.
        
        This method changes the registration state to submitted,
        indicating that the subject selection is ready for review.
        """
        self.state = 'submitted'

    @api.model_create_multi
    def create(self, vals_list):
        """Create new subject registrations with sequence numbers.

        This method:
        1. Generates a unique sequence number for each registration
        2. Creates the registration records with the sequence numbers

        Args:
            vals_list (list): List of dictionaries containing field values

        Returns:
            recordset: Created subject registration records
        """
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'op.subject.registration') or '/'
        return super(OpSubjectRegistration, self).create(vals_list)

    def get_subjects(self):
        """Update compulsory subjects based on the selected course.
        
        This method:
        1. Retrieves all subjects from the selected course
        2. Filters for compulsory subjects
        3. Updates the compulsory_subject_ids field
        """
        for record in self:
            subject_ids = []
            if record.course_id and record.course_id.subject_ids:
                for subject in record.course_id.subject_ids:
                    if subject.subject_type == 'compulsory':
                        subject_ids.append(subject.id)
            record.compulsory_subject_ids = [(6, 0, subject_ids)]

    @api.constrains('min_unit_load', 'max_unit_load')
    def _check_unit_load(self):
        """Validate unit load constraints.

        Ensures that:
        - Minimum unit load is not greater than maximum unit load
        - Both values are non-negative

        Raises:
            ValidationError: If unit load constraints are violated
        """
        for record in self:
            if record.min_unit_load and record.max_unit_load and \
               record.min_unit_load > record.max_unit_load:
                raise ValidationError(_('Minimum unit load cannot be greater than maximum unit load.'))
