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

from odoo import fields, models


class OpActivity(models.Model):
    """
    Activity Model for managing student activities.
    Tracks activities performed by students with faculty supervision.
    """
    _name = "op.activity"
    _description = "Student Activity"
    _rec_name = "student_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_faculty(self):
        """Get the default faculty based on current user."""
        return self.env['op.faculty'].search([
            ('user_id', '=', self._uid)
        ], limit=1) or False

    # Student Information
    student_id = fields.Many2one('op.student', 'Student', required=True)
    faculty_id = fields.Many2one('op.faculty', string='Faculty',
                                 default=lambda self: self._default_faculty())
    
    # Activity Details
    type_id = fields.Many2one('op.activity.type', 'Activity Type')
    description = fields.Text('Description')
    date = fields.Date('Date', default=fields.Date.today())
    
    # Status
    active = fields.Boolean(default=True)
