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

from odoo import api, fields, models


class OpClassroom(models.Model):
    """
    Classroom Management Model
    
    This model represents a physical classroom in the educational institution.
    It manages classroom details, capacity, facilities, and assets.
    """
    _name = "op.classroom"
    _description = "Classroom"
    _order = "name"

    # Basic Information
    name = fields.Char(
        string='Name',
        size=16,
        required=True,
        help="Name of the classroom"
    )
    code = fields.Char(
        string='Code',
        size=16,
        required=True,
        help="Unique identifier code for the classroom"
    )
    
    # Academic Information
    course_id = fields.Many2one(
        'op.course',
        string='Course',
        help="Associated course for this classroom"
    )
    batch_id = fields.Many2one(
        'op.batch',
        string='Batch',
        help="Associated batch for this classroom"
    )
    
    # Capacity and Facilities
    capacity = fields.Integer(
        string='No Of Person',
        help="Maximum number of persons that can be accommodated"
    )
    facilities = fields.One2many(
        'op.facility.line',
        'classroom_id',
        string='Facility Lines',
        help="Facilities available in this classroom"
    )
    
    # Assets
    asset_line = fields.One2many(
        'op.asset',
        'asset_id',
        string='Asset',
        help="Assets assigned to this classroom"
    )
    
    # Status
    active = fields.Boolean(
        default=True,
        help="If unchecked, the classroom will be hidden from the system"
    )

    # Constraints
    _sql_constraints = [
        ('unique_classroom_code',
         'unique(code)',
         'Code should be unique per classroom!')
    ]

    @api.onchange('course_id')
    def onchange_course(self):
        """
        Reset batch when course is changed
        """
        self.batch_id = False
