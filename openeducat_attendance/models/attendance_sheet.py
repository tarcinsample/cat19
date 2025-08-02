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


class OpAttendanceSheet(models.Model):
    _name = "op.attendance.sheet"
    _inherit = ["mail.thread"]
    _description = "Attendance Sheet"
    _order = "attendance_date desc"

    name = fields.Char('Name', readonly=True, size=32)
    register_id = fields.Many2one(
        'op.attendance.register', 'Register', required=True,
        tracking=True)
    course_id = fields.Many2one(
        'op.course', related='register_id.course_id', store=True,
        readonly=True)
    batch_id = fields.Many2one(
        'op.batch', 'Batch', related='register_id.batch_id', store=True,
        readonly=True)
    session_id = fields.Many2one('op.session', 'Session')
    attendance_date = fields.Date(
        'Date', required=True, default=lambda self: fields.Date.today(),
        tracking=True)
    attendance_line = fields.One2many(
        'op.attendance.line', 'attendance_id', 'Attendance Line')
    faculty_id = fields.Many2one('op.faculty', 'Faculty')
    active = fields.Boolean(default=True)

    state = fields.Selection(
        [('draft', 'Draft'), ('start', 'Attendance Start'),
         ('done', 'Attendance Taken'), ('cancel', 'Cancelled')],
        'Status', default='draft', tracking=True)

    def attendance_draft(self):
        """Set attendance sheet to draft state for editing."""
        self.ensure_one()
        if self.attendance_line:
            raise ValidationError(_(
                "Cannot set to draft when attendance lines exist. "
                "Please remove attendance lines first."))
        self.state = 'draft'

    def attendance_start(self):
        """Start attendance process and validate register."""
        self.ensure_one()
        if not self.register_id:
            raise ValidationError(_("Attendance register must be selected."))
        if not self.attendance_date:
            raise ValidationError(_("Attendance date is required."))
        self.state = 'start'

    def attendance_done(self):
        """Complete attendance taking and validate data."""
        self.ensure_one()
        if not self.attendance_line:
            raise ValidationError(_(
                "Cannot complete attendance without any attendance lines."))
        self.state = 'done'

    def attendance_cancel(self):
        """Cancel attendance sheet."""
        self.ensure_one()
        self.state = 'cancel'

    _sql_constraints = [
        ('unique_register_sheet',
         'unique(register_id,session_id,attendance_date)',
         'Sheet must be unique per Register/Session.'),
    ]

    @api.constrains('attendance_date', 'register_id')
    def _check_attendance_date(self):
        """Validate attendance date constraints.
        
        Raises:
            ValidationError: If attendance date is invalid
        """
        for record in self:
            if not record.attendance_date:
                continue
                
            today = fields.Date.today()
            if record.attendance_date > today:
                raise ValidationError(_(
                    "Attendance date (%s) cannot be in the future.") % 
                    record.attendance_date)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate attendance sheet sequence.
        
        Ensures proper sequence generation with error handling.
        """
        for vals in vals_list:
            sequence = self.env['ir.sequence'].next_by_code('op.attendance.sheet')
            if not sequence:
                raise ValidationError(_(
                    "Unable to generate attendance sheet number. "
                    "Please check sequence configuration."))
                    
            register_id = vals.get('register_id')
            if not register_id:
                raise ValidationError(_("Attendance register is required."))
                
            register = self.env['op.attendance.register'].browse(register_id)
            if not register.exists():
                raise ValidationError(_("Invalid attendance register."))
                
            vals['name'] = f"{register.code}{sequence}"
        return super(OpAttendanceSheet, self).create(vals_list)

    def generate_attendance_lines(self):
        """Generate attendance lines for all students in the batch.
        
        Creates attendance lines for students not already present.
        """
        self.ensure_one()
        if not self.register_id:
            raise ValidationError(_("Attendance register must be selected."))
            
        # Find all students in the batch
        students = self.env['op.student'].search([
            ('course_detail_ids.course_id', '=', self.register_id.course_id.id),
            ('course_detail_ids.batch_id', '=', self.register_id.batch_id.id),
            ('active', '=', True)
        ])
        
        if not students:
            raise ValidationError(_(
                "No students found for the selected course and batch."))
        
        # Get existing attendance lines
        existing_student_ids = self.attendance_line.mapped('student_id.id')
        
        # Create attendance lines for new students
        attendance_lines = []
        for student in students:
            if student.id not in existing_student_ids:
                attendance_lines.append({
                    'attendance_id': self.id,
                    'student_id': student.id,
                    'present': False,  # Default to absent for manual marking
                })
        
        if attendance_lines:
            self.env['op.attendance.line'].create(attendance_lines)
            return len(attendance_lines)
        
        return 0
