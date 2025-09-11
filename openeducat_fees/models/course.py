##############################################################################
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
##############################################################################

from odoo import api, fields, models


class OpCourse(models.Model):
    """Extended course model with fees term configuration.
    
    This model adds fee payment term configuration to courses,
    allowing different fee structures for different courses.
    """
    _inherit = "op.course"

    fees_term_id = fields.Many2one(
        'op.fees.terms', 'Fees Term',
        domain="[('active', '=', True)]",
        help="Default fee payment term for this course")
    fees_amount = fields.Monetary(
        'Course Fees',
        currency_field='currency_id',
        help="Base fee amount for this course")
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id,
        help="Currency for fee calculations")
    
    @api.onchange('fees_term_id')
    def _onchange_fees_term_id(self):
        """Update currency when fee term changes."""
        if self.fees_term_id and self.fees_term_id.company_id:
            self.currency_id = self.fees_term_id.company_id.currency_id.id
