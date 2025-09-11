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


class GradingAssigment(models.Model):
    _name = 'grading.assignment'
    _description = "Grading Assignment"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, help="Assignment title or name")
    course_id = fields.Many2one('op.course', 'Course', required=True, tracking=True,
                                help="Course for which this assignment is created")
    subject_id = fields.Many2one('op.subject', string='Subject', tracking=True,
                                 domain="[('id', 'in', course_subject_ids)]",
                                 help="Subject within the course")
    course_subject_ids = fields.Many2many(
        'op.subject', related='course_id.subject_ids', readonly=True,
        help="Available subjects for the selected course")
    issued_date = fields.Datetime('Issued Date', required=True, tracking=True,
                                  help="Date when assignment was issued")
    end_date = fields.Datetime('End Date', tracking=True,
                              help="Assignment end date (optional)")
    assignment_type = fields.Many2one('grading.assignment.type',
                                      string='Assignment Type', required=True,
                                      help="Type/category of assignment")
    faculty_id = fields.Many2one(
        'op.faculty', 'Faculty', default=lambda self: self.env[
            'op.faculty'].search([('user_id', '=', self.env.uid)], limit=1),
        required=True, tracking=True, help="Faculty member who created this assignment")
    point = fields.Float('Points', help="Maximum points for this assignment")


class OpAssignment(models.Model):
    _name = "op.assignment"
    _inherit = "mail.thread"
    _description = "Assignment"
    _order = "submission_date DESC"
    _inherits = {"grading.assignment": "grading_assignment_id"}

    batch_id = fields.Many2one('op.batch', 'Batch', required=True, tracking=True,
                               domain="[('course_id', '=', course_id)]",
                               help="Batch for which this assignment is created")
    marks = fields.Float('Marks', tracking=True)
    description = fields.Text('Description', required=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('publish', 'Published'),
        ('finish', 'Finished'), ('cancel', 'Cancel'),
    ], 'State', required=True, default='draft', tracking=True)
    submission_date = fields.Datetime('Submission Date', required=True,
                                      tracking=True)
    allocation_ids = fields.Many2many('op.student', string='Allocated To', tracking=True,
                                      help="Students who can submit this assignment")
    assignment_sub_line = fields.One2many('op.assignment.sub.line',
                                          'assignment_id', 'Submission')
    reviewer = fields.Many2one('op.faculty', 'Reviewer')
    active = fields.Boolean(default=True)
    grading_assignment_id = fields.Many2one('grading.assignment', 'Grading Assignment',
                                            required=True, ondelete="cascade")
    assignment_sub_line_count = fields.Integer(
        'Submissions', compute="_compute_assignment_count_compute",
        help="Total number of assignment submissions")
    courses_subjects = fields.Many2many('op.subject')

    @api.constrains('issued_date', 'submission_date')
    def check_dates(self):
        """Validate assignment date constraints.
        
        Raises:
            ValidationError: If submission date is before issue date
        """
        for record in self:
            if not record.issued_date or not record.submission_date:
                continue
                
            issued_date = record.issued_date.date() if hasattr(record.issued_date, 'date') and record.issued_date else False
            submission_date = record.submission_date.date() if hasattr(record.submission_date, 'date') and record.submission_date else False
            
            if issued_date and submission_date and issued_date > submission_date:
                raise ValidationError(_(
                    "Submission Date (%s) cannot be set before Issue Date (%s).") % (
                    submission_date, issued_date))
    
    @api.constrains('issued_date', 'end_date')
    def check_end_date(self):
        """Validate assignment end date constraints.
        
        Raises:
            ValidationError: If end date is before issue date
        """
        for record in self:
            if not record.issued_date or not record.end_date:
                continue
                
            issued_date = record.issued_date.date() if hasattr(record.issued_date, 'date') and record.issued_date else False
            end_date = record.end_date.date() if hasattr(record.end_date, 'date') and record.end_date else False
            
            if issued_date and end_date and issued_date > end_date:
                raise ValidationError(_(
                    "End Date (%s) cannot be set before Issue Date (%s).") % (
                    end_date, issued_date))
    
    @api.constrains('batch_id', 'state')
    def _check_batch_required(self):
        """Ensure batch_id is not cleared on non-draft assignments.
        
        Raises:
            ValidationError: If batch_id is empty on non-draft assignment
        """
        for record in self:
            if record.state and record.state != 'draft' and not record.batch_id:
                raise ValidationError(_("Batch is required for non-draft assignments."))

    @api.depends('assignment_sub_line')
    def _compute_assignment_count_compute(self):
        """Compute assignment submission count.
        
        Efficiently counts total submissions for this assignment.
        """
        for record in self:
            record.assignment_sub_line_count = len(record.assignment_sub_line)

    @api.onchange('course_id')
    def onchange_course(self):
        """Handle course change to update related fields.
        
        Updates batch and subject domains when course changes.
        """
        # Only clear fields if in draft state AND when actually changing course
        # This prevents clearing required fields during other operations
        if self.state == 'draft' and self._origin.course_id != self.course_id:
            # Only clear batch if it doesn't belong to the new course
            if self.batch_id and self.course_id and self.batch_id.course_id != self.course_id:
                self.batch_id = False
            # Only clear subject if it doesn't belong to the new course
            if self.subject_id and self.course_id and self.subject_id not in self.course_id.subject_ids:
                self.subject_id = False
        
        self.courses_subjects = False
        
        if self.course_id:
            # Update courses_subjects
            self.courses_subjects = self.course_id.subject_ids
            
            # Return domain for subject_id
            return {
                'domain': {
                    'subject_id': [('id', 'in', self.course_id.subject_ids.ids)],
                    'batch_id': [('course_id', '=', self.course_id.id)]
                }
            }
        
        return {
            'domain': {
                'subject_id': [],
                'batch_id': []
            }
        }

    def act_publish(self):
        """Publish assignment for students to view and submit.
        
        Validates required fields before publishing.
        """
        self.ensure_one()
        if not self.description:
            raise ValidationError(_("Description is required before publishing assignment."))
        if not self.allocation_ids:
            raise ValidationError(_("Students must be allocated before publishing assignment."))
        self.state = 'publish'
        return True

    def act_finish(self):
        """Finish assignment and stop accepting submissions.
        
        Validates that assignment is published before finishing.
        """
        self.ensure_one()
        if self.state != 'publish':
            raise ValidationError(_("Assignment must be published before finishing."))
        self.state = 'finish'
        return True

    def act_cancel(self):
        """Cancel assignment.
        
        Validates that no submissions exist before cancelling.
        """
        self.ensure_one()
        if self.assignment_sub_line:
            raise ValidationError(_(
                "Cannot cancel assignment with existing submissions. "
                "Please handle submissions first."))
        self.state = 'cancel'

    def act_set_to_draft(self):
        """Reset assignment to draft state for editing."""
        self.ensure_one()
        self.state = 'draft'

    def get_assignment_submissions(self):
        """Open assignment submissions view.
        
        Returns action to view all submissions for this assignment.
        
        Returns:
            dict: Action dictionary for opening submissions view
        """
        self.ensure_one()
        return {
            'name': _('Assignment Submissions'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.assignment.sub.line',
            'domain': [('assignment_id', '=', self.id)],
            'target': 'current',
            'context': {'default_assignment_id': self.id}
        }
