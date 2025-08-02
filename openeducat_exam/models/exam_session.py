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


class OpExamSession(models.Model):
    _name = "op.exam.session"
    _inherit = ["mail.thread"]
    _description = "Exam Session"

    name = fields.Char(
        'Exam Session', size=256, required=True, tracking=True)
    course_id = fields.Many2one(
        'op.course', 'Course', required=True, tracking=True)
    batch_id = fields.Many2one(
        'op.batch', 'Batch', required=True, tracking=True)
    exam_code = fields.Char(
        'Exam Session Code', size=16,
        required=True, tracking=True)
    start_date = fields.Date(
        'Start Date', required=True, tracking=True)
    end_date = fields.Date(
        'End Date', required=True, tracking=True)
    exam_ids = fields.One2many(
        'op.exam', 'session_id', 'Exam(s)')
    exam_type = fields.Many2one(
        'op.exam.type', 'Exam Type',
        required=True, tracking=True)
    evaluation_type = fields.Selection(
        [('normal', 'Normal'), ('grade', 'Grade')],
        'Evolution Type', default="normal",
        required=True, tracking=True)
    venue = fields.Many2one(
        'res.partner', 'Venue', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('schedule', 'Scheduled'),
        ('held', 'Held'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], 'State', default='draft', tracking=True)
    active = fields.Boolean(default=True)
    exams_count = fields.Integer(
        compute='_compute_exams_count', string="Exams")

    _sql_constraints = [
        ('unique_exam_session_code',
         'unique(exam_code)', 'Code should be unique per exam session!')]

    @api.depends('exam_ids')
    def _compute_exams_count(self):
        """Compute exam count efficiently.
        
        Uses relation field length for better performance.
        """
        for rec in self:
            rec.exams_count = len(rec.exam_ids)

    @api.constrains('start_date', 'end_date')
    def _check_date_time(self):
        """Validate exam session date constraints.
        
        Raises:
            ValidationError: If end date is before start date
        """
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_(
                        "End Date (%s) cannot be set before Start Date (%s).") % (
                        record.end_date, record.start_date))

    @api.constrains('course_id', 'batch_id')
    def _check_batch_course_consistency(self):
        """Validate batch belongs to selected course.
        
        Raises:
            ValidationError: If batch doesn't belong to the course
        """
        for record in self:
            if record.batch_id and record.course_id:
                if record.batch_id.course_id != record.course_id:
                    raise ValidationError(_(
                        "Batch '%s' does not belong to course '%s'.") % (
                        record.batch_id.name, record.course_id.name))

    @api.onchange('course_id')
    def onchange_course(self):
        """Handle course change to update batch domain."""
        self.batch_id = False
        
        if self.course_id:
            return {
                'domain': {
                    'batch_id': [('course_id', '=', self.course_id.id), ('active', '=', True)]
                }
            }
        
        return {
            'domain': {
                'batch_id': []
            }
        }

    def act_draft(self):
        """Reset exam session to draft state for editing."""
        self.ensure_one()
        if self.state == 'done':
            raise ValidationError(_(
                "Cannot reset completed exam session to draft."))
        self.state = 'draft'

    def act_schedule(self):
        """Schedule exam session and validate configuration."""
        self.ensure_one()
        if not self.course_id or not self.batch_id:
            raise ValidationError(_(
                "Course and batch are required to schedule exam session."))
        if not self.exam_type:
            raise ValidationError(_(
                "Exam type is required to schedule exam session."))
        self.state = 'schedule'

    def act_held(self):
        """Mark exam session as held."""
        self.ensure_one()
        if self.state != 'schedule':
            raise ValidationError(_(
                "Exam session can only be marked as held from scheduled state."))
        if not self.exam_ids:
            raise ValidationError(_(
                "Cannot mark session as held without any exams."))
        self.state = 'held'

    def act_done(self):
        """Complete exam session and validate all exams are done."""
        self.ensure_one()
        if self.state not in ['held', 'schedule']:
            raise ValidationError(_(
                "Exam session can only be completed from held or scheduled state."))
                
        # Check all exams are completed
        pending_exams = self.exam_ids.filtered(lambda e: e.state != 'done')
        if pending_exams:
            exam_names = ', '.join(pending_exams.mapped('name'))
            raise ValidationError(_(
                "Cannot complete session. The following exams are not done: %s") % 
                exam_names)
                
        self.state = 'done'

    def act_cancel(self):
        """Cancel exam session and associated exams."""
        self.ensure_one()
        if self.state == 'done':
            raise ValidationError(_(
                "Cannot cancel completed exam session."))
                
        # Cancel all associated exams
        draft_exams = self.exam_ids.filtered(lambda e: e.state in ['draft', 'schedule'])
        if draft_exams:
            draft_exams.act_cancel()
            
        self.state = 'cancel'

    def get_exam(self):
        """Open exams view for this session.
        
        Returns action to view all exams in this session.
        """
        self.ensure_one()
        return {
            'name': _('Exams - %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'op.exam',
            'domain': [('session_id', '=', self.id)],
            'context': {
                'default_session_id': self.id,
                'default_course_id': self.course_id.id,
                'default_batch_id': self.batch_id.id
            },
            'target': 'current',
        }
        
    def create_exam(self):
        """Create new exam for this session.
        
        Returns action to create new exam with session context.
        """
        self.ensure_one()
        if self.state not in ['draft', 'schedule']:
            raise ValidationError(_(
                "Cannot create exams for session in '%s' state.") % 
                dict(self._fields['state'].selection)[self.state])
                
        return {
            'name': _('New Exam'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'op.exam',
            'context': {
                'default_session_id': self.id,
                'default_course_id': self.course_id.id,
                'default_batch_id': self.batch_id.id
            },
            'target': 'current',
        }
