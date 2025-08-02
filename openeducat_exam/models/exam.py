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

import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpExam(models.Model):
    _name = "op.exam"
    _inherit = "mail.thread"
    _description = "Exam"

    session_id = fields.Many2one('op.exam.session', 'Exam Session',
                                 domain=[('state', '=', 'schedule')])
    course_id = fields.Many2one(
        'op.course', related='session_id.course_id', store=True,
        readonly=True)
    batch_id = fields.Many2one(
        'op.batch', 'Batch', related='session_id.batch_id', store=True,
        readonly=True)
    subject_id = fields.Many2one('op.subject', 'Subject', required=True)
    exam_code = fields.Char('Exam Code', size=16, required=True)
    attendees_line = fields.One2many(
        'op.exam.attendees', 'exam_id', 'Attendees', readonly=True)
    start_time = fields.Datetime('Start Time', required=True)
    end_time = fields.Datetime('End Time', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('schedule', 'Scheduled'), ('held', 'Held'),
         ('result_updated', 'Result Updated'),
         ('cancel', 'Cancelled'), ('done', 'Done')], 'State',
        readonly=True, default='draft', tracking=True)
    note = fields.Text('Note')
    responsible_id = fields.Many2many('op.faculty', string='Responsible')
    name = fields.Char('Exam', size=256, required=True)
    total_marks = fields.Integer('Total Marks', required=True)
    min_marks = fields.Integer('Passing Marks', required=True)
    active = fields.Boolean(default=True)
    attendees_count = fields.Integer(string='Attendees Count',
                                     compute='_compute_attendees_count')
    results_entered = fields.Boolean(string='Results Entered',
                                     compute='_compute_results_entered', store=True)

    _sql_constraints = [
        ('unique_exam_code',
         'unique(exam_code)', 'Code should be unique per exam!')]

    @api.constrains('total_marks', 'min_marks')
    def _check_marks(self):
        for record in self:
            if record.total_marks <= 0 or record.min_marks <= 0:
                raise ValidationError(_('Enter proper marks!'))
            if record.min_marks > record.total_marks:
                raise ValidationError(_(
                    "Passing marks cannot be greater than total marks."))

    @api.constrains('start_time', 'end_time', 'session_id')
    def _check_date_time(self):
        for record in self:
            if not record.session_id:
                continue

            session_start_date = fields.Date.from_string(record.session_id.start_date)
            session_end_date = fields.Date.from_string(
                record.session_id.end_date)

            session_start_dt = datetime.datetime.combine(
                session_start_date, datetime.time.min)
            session_end_dt = datetime.datetime.combine(
                session_end_date, datetime.time.max)

            start_time_dt = fields.Datetime.from_string(record.start_time)
            end_time_dt = fields.Datetime.from_string(record.end_time)

            if start_time_dt and end_time_dt:
                if start_time_dt > end_time_dt:
                    raise ValidationError(
                        _('End Time cannot be set before Start Time.'))
                elif start_time_dt == end_time_dt:
                    raise ValidationError(
                        _("End time and start time cannot be set at the same time."))
                elif start_time_dt < session_start_dt or \
                        start_time_dt > session_end_dt or \
                        end_time_dt < session_start_dt or \
                        end_time_dt > session_end_dt:
                    raise ValidationError(
                        _('Exam Time should be within the Exam Session Dates.'))

    def open_exam_attendees(self):
        """Open exam attendees view.
        
        Returns action to view and manage exam attendees.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "op.exam.attendees",
            "domain": [("exam_id", "=", self.id)],
            "name": _("Exam Attendees - %s") % self.name,
            "view_mode": "list,form",
            "context": {
                'default_exam_id': self.id,
                'default_course_id': self.course_id.id,
                'default_batch_id': self.batch_id.id
            },
            "target": "current",
        }
        
    def _generate_attendees(self):
        """Generate attendee records for all students in the batch.
        
        Creates attendee records for students enrolled in the course/batch.
        """
        self.ensure_one()
        if not self.session_id or not self.session_id.batch_id:
            raise ValidationError(_(
                "Exam session and batch are required to generate attendees."))
            
        # Find all students in the batch
        students = self.env['op.student'].search([
            ('course_detail_ids.course_id', '=', self.course_id.id),
            ('course_detail_ids.batch_id', '=', self.batch_id.id),
            ('active', '=', True)
        ])
        
        if not students:
            raise ValidationError(_(
                "No students found for course '%s' and batch '%s'.") % (
                self.course_id.name, self.batch_id.name))
        
        # Create attendee records
        attendee_vals = []
        for student in students:
            attendee_vals.append({
                'exam_id': self.id,
                'student_id': student.id,
                'status': 'present'  # Default to present
            })
        
        if attendee_vals:
            self.env['op.exam.attendees'].create(attendee_vals)
            return len(attendee_vals)
        
        return 0

    @api.depends('attendees_line')
    def _compute_attendees_count(self):
        """Compute attendees count efficiently.
        
        Uses relation field length instead of database search.
        """
        for record in self:
            record.attendees_count = len(record.attendees_line)

    @api.depends('attendees_line', 'attendees_line.marks')
    def _compute_results_entered(self):
        for record in self:
            record.results_entered = any(
                attendee.marks is not False and attendee.marks is not None
                for attendee in record.attendees_line
            )

    @api.constrains('subject_id', 'start_time', 'end_time')
    def _check_overlapping_times(self):
        for record in self:
            if not record.subject_id or not record.start_time or not record.end_time:
                continue

            existing_exams = self.env['op.exam'].search([
                ('subject_id', '=', record.subject_id.id),
                ('id', '!=', record.id),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time),
            ])
            if existing_exams:
                raise ValidationError(_(
                    'The exam time overlaps with an existing exam for the same '
                    'subject : %s' %
                    ', '.join(existing_exams.mapped('name'))
                ))

    def act_result_updated(self):
        """Update exam state to result updated.
        
        Validates that all attendees have marks entered.
        """
        self.ensure_one()
        if self.state != 'held':
            raise ValidationError(_(
                "Results can only be updated for exams in 'Held' state."))
                
        # Validate that results have been entered
        if not self.attendees_line:
            raise ValidationError(_(
                "Cannot update results without any attendees."))
                
        missing_results = self.attendees_line.filtered(
            lambda a: a.status == 'present' and (a.marks is False or a.marks is None))
        if missing_results:
            student_names = ', '.join(missing_results.mapped('student_id.name'))
            raise ValidationError(_(
                "Results are missing for the following present students: %s") % 
                student_names)
                
        self.state = 'result_updated'

    def act_done(self):
        """Mark exam as completed.
        
        Validates that exam is in proper state for completion.
        """
        for record in self:
            if record.state not in ['result_updated', 'held']:
                raise ValidationError(_(
                    "Exam can only be marked as 'Done' from 'Held' "
                    "or 'Result Updated' state."))
            record.state = 'done'

    def act_draft(self):
        """Reset exam to draft state for editing."""
        for record in self:
            if record.state == 'done':
                raise ValidationError(_(
                    "Cannot reset completed exam to draft state."))
            record.state = 'draft'

    def act_cancel(self):
        """Cancel exam and remove associated attendees.
        
        Validates exam state and removes attendee records.
        """
        for exam in self:
            if exam.state == 'done':
                raise ValidationError(_(
                    "Cannot cancel an exam that is already 'Done'."))
            
            # Check if results have been generated
            if exam.state == 'result_updated' and exam.attendees_line.filtered('marks'):
                raise ValidationError(_(
                    "Cannot cancel exam with entered results. "
                    "Please remove results first."))

            # Remove attendees using the relation field for better performance
            if exam.attendees_line:
                exam.attendees_line.unlink()
            exam.state = 'cancel'
        return True

    def act_schedule(self):
        """Schedule exam and generate attendees.
        
        Validates exam configuration and creates attendee records.
        """
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    "Exam can only be scheduled from 'Draft' state."))
                    
            # Validate required fields
            if not record.session_id:
                raise ValidationError(_("Exam session is required to schedule exam."))
            if not record.subject_id:
                raise ValidationError(_("Subject is required to schedule exam."))
            if not record.start_time or not record.end_time:
                raise ValidationError(_("Start time and end time are required."))
                
            record.state = 'schedule'
            
            # Auto-generate attendees if none exist
            if not record.attendees_line:
                record._generate_attendees()

    def act_held(self):
        """Mark exam as held.
        
        Validates that exam is scheduled and has attendees.
        """
        for record in self:
            if record.state != 'schedule':
                raise ValidationError(_(
                    "Exam can only be marked as 'Held' from 'Scheduled' state."))
                    
            if not record.attendees_line:
                raise ValidationError(_(
                    "Cannot mark exam as held without any attendees."))
                    
            record.state = 'held'
