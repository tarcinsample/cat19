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

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class OpSession(models.Model):
    _inherit = "op.session"

    attendance_sheet = fields.One2many('op.attendance.sheet',
                                       'session_id', string='Session')

    def get_attendance(self):
        """Get or create attendance sheet for this session.
        
        Returns action to open attendance sheet(s) for the session.
        Optimized to reduce database queries and improve error handling.
        """
        self.ensure_one()
        
        if not self.course_id or not self.batch_id:
            raise ValidationError(_(
                "Session must have course and batch configured for attendance."))
        
        # Find existing attendance sheets for this session
        sheets = self.env['op.attendance.sheet'].search([
            ('session_id', '=', self.id)
        ])
        
        # Find attendance register for this course/batch
        register = self.env['op.attendance.register'].search([
            ('course_id', '=', self.course_id.id),
            ('batch_id', '=', self.batch_id.id)
        ], limit=1)
        
        if not register:
            raise ValidationError(_(
                "No attendance register found for course '%s' and batch '%s'. "
                "Please create an attendance register first.") % (
                self.course_id.name, self.batch_id.name))
        
        context = {
            'default_session_id': self.id,
            'default_register_id': register.id
        }
        
        # If single sheet exists, open it directly
        if len(sheets) == 1:
            return {
                'name': _('Attendance Sheet'),
                'view_mode': 'form',
                'res_model': 'op.attendance.sheet',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': sheets.id,
                'context': context
            }
        
        # If multiple sheets exist, show list view
        elif len(sheets) > 1:
            return {
                'name': _('Attendance Sheets'),
                'view_mode': 'list,form',
                'res_model': 'op.attendance.sheet',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('session_id', '=', self.id)],
                'context': context
            }
        
        # No sheets exist, create new one
        else:
            return {
                'name': _('New Attendance Sheet'),
                'view_mode': 'form',
                'res_model': 'op.attendance.sheet',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': context
            }
