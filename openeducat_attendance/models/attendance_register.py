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


class OpAttendanceRegister(models.Model):
    _name = "op.attendance.register"
    _inherit = ["mail.thread"]
    _description = "Attendance Register"
    _order = "id DESC"
    _rec_name = "name"

    name = fields.Char(
        'Name', size=16, required=True, tracking=True)
    code = fields.Char(
        'Code', size=16, required=True, tracking=True)
    course_id = fields.Many2one(
        'op.course', 'Course', required=True, tracking=True)
    batch_id = fields.Many2one(
        'op.batch', 'Batch', required=True, tracking=True)
    subject_id = fields.Many2one(
        'op.subject', 'Subject', tracking=True,
        domain="[('id', 'in', course_subject_ids)]",
        help="Subject for which attendance will be tracked")
    course_subject_ids = fields.Many2many(
        'op.subject', related='course_id.subject_ids', readonly=True,
        help="Available subjects for the selected course")
    attendance_sheet_count = fields.Integer(
        'Total Sheets', compute='_compute_attendance_statistics',
        help="Total number of attendance sheets created")
    total_students = fields.Integer(
        'Total Students', compute='_compute_attendance_statistics',
        help="Total number of students in this batch")
    active = fields.Boolean(default=True)

    attendance_sheet_ids = fields.One2many(
        'op.attendance.sheet', 'register_id', 'Attendance Sheets',
        help="All attendance sheets created for this register")

    _sql_constraints = [
        ('unique_attendance_register_code',
         'unique(code)', 'Code should be unique per attendance register!'),
        ('unique_course_batch_subject',
         'unique(course_id, batch_id, subject_id)',
         'Only one register per course/batch/subject combination is allowed!')]

    def create_attendance_sheet(self):
        """Create new attendance sheet for this register.
        
        Returns action to open the new attendance sheet.
        """
        self.ensure_one()
        
        # Check if sheet already exists for today
        today = fields.Date.today()
        existing_sheet = self.env['op.attendance.sheet'].search([
            ('register_id', '=', self.id),
            ('attendance_date', '=', today)
        ], limit=1)
        
        if existing_sheet:
            return {
                'name': _('Attendance Sheet'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'op.attendance.sheet',
                'res_id': existing_sheet.id,
                'target': 'current'
            }
        
        # Create new sheet
        sheet = self.env['op.attendance.sheet'].create({
            'register_id': self.id,
            'attendance_date': today
        })
        
        return {
            'name': _('Attendance Sheet'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'op.attendance.sheet',
            'res_id': sheet.id,
            'target': 'current'
        }

    @api.depends('attendance_sheet_ids')
    def _compute_attendance_statistics(self):
        """Compute attendance statistics for the register.
        
        Efficiently calculates total sheets and students.
        """
        for record in self:
            # Count attendance sheets
            record.attendance_sheet_count = len(record.attendance_sheet_ids)
            
            # Count total students in batch
            if record.batch_id:
                students = self.env['op.student'].search_count([
                    ('course_detail_ids.course_id', '=', record.course_id.id),
                    ('course_detail_ids.batch_id', '=', record.batch_id.id),
                    ('active', '=', True)
                ])
                record.total_students = students
            else:
                record.total_students = 0

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
        """Handle course change to update related fields.
        
        Updates batch and subject domains when course changes.
        """
        self.batch_id = False
        self.subject_id = False
        
        if self.course_id:
            return {
                'domain': {
                    'batch_id': [('course_id', '=', self.course_id.id), ('active', '=', True)],
                    'subject_id': [('id', 'in', self.course_id.subject_ids.ids)]
                }
            }
        
        return {
            'domain': {
                'batch_id': [],
                'subject_id': []
            }
        }
