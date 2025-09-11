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


class OpAttendanceLine(models.Model):
    _name = "op.attendance.line"
    _inherit = ["mail.thread"]
    _rec_name = "attendance_id"
    _description = "Attendance Lines"
    _order = "attendance_date desc"

    attendance_id = fields.Many2one(
        'op.attendance.sheet', 'Attendance Sheet', required=True,
        tracking=True, ondelete="cascade")
    student_id = fields.Many2one(
        'op.student', 'Student', required=True, tracking=True)
    present = fields.Boolean(
        'Present', tracking=True)
    excused = fields.Boolean(
        'Absent Excused', tracking=True)
    absent = fields.Boolean('Absent Unexcused', tracking=True)
    late = fields.Boolean('Late', tracking=True)
    course_id = fields.Many2one(
        'op.course', 'Course',
        related='attendance_id.register_id.course_id', store=True,
        readonly=True)
    batch_id = fields.Many2one(
        'op.batch', 'Batch',
        related='attendance_id.register_id.batch_id', store=True,
        readonly=True)
    remark = fields.Char('Remark', size=256, tracking=True)
    attendance_date = fields.Date(
        'Date', related='attendance_id.attendance_date', store=True,
        readonly=True, tracking=True)
    register_id = fields.Many2one(
        related='attendance_id.register_id', store=True)
    active = fields.Boolean(default=True)
    attendance_type_id = fields.Many2one(
        'op.attendance.type', 'Attendance Type',
        required=False, tracking=True)
    state = fields.Selection(related = "attendance_id.state")

    _sql_constraints = [
        ('unique_student',
         'unique(student_id,attendance_id,attendance_date)',
         'Student must be unique per Attendance.'),
    ]

    @api.constrains('present', 'excused', 'absent', 'late')
    def _check_attendance_status(self):
        """Validate attendance status constraints.
        
        Ensures only one attendance status is selected.
        """
        for record in self:
            statuses = [record.present, record.excused, record.absent, record.late]
            true_count = sum(statuses)
            
            if true_count == 0:
                raise ValidationError(_(
                    "At least one attendance status must be selected for student '%s'.") % 
                    record.student_id.name)
            elif true_count > 1:
                raise ValidationError(_(
                    "Only one attendance status can be selected for student '%s'.") % 
                    record.student_id.name)

    @api.onchange('attendance_type_id')
    def onchange_attendance_type(self):
        """Update attendance status based on attendance type."""
        if self.attendance_type_id:
            self.present = self.attendance_type_id.present
            self.excused = self.attendance_type_id.excused
            self.absent = self.attendance_type_id.absent
            self.late = self.attendance_type_id.late

    @api.onchange('present')
    def onchange_present(self):
        """Clear other attendance statuses when present is marked."""
        if self.present:
            self.late = False
            self.excused = False
            self.absent = False
            self.attendance_type_id = self.env['op.attendance.type'].search([
                ('present', '=', True)
            ], limit=1)

    @api.onchange('absent')
    def onchange_absent(self):
        """Clear other attendance statuses when absent is marked."""
        if self.absent:
            self.present = False
            self.late = False
            self.excused = False
            self.attendance_type_id = self.env['op.attendance.type'].search([
                ('absent', '=', True)
            ], limit=1)

    @api.onchange('excused')
    def onchange_excused(self):
        """Clear other attendance statuses when excused is marked."""
        if self.excused:
            self.present = False
            self.late = False
            self.absent = False
            self.attendance_type_id = self.env['op.attendance.type'].search([
                ('excused', '=', True)
            ], limit=1)

    @api.onchange('late')
    def onchange_late(self):
        """Clear other attendance statuses when late is marked."""
        if self.late:
            self.present = False
            self.excused = False
            self.absent = False
            self.attendance_type_id = self.env['op.attendance.type'].search([
                ('late', '=', True)
            ], limit=1)
