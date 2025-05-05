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


class OpBatch(models.Model):
    """Batch model for OpenEduCat.

    This model manages student batches within the institution,
    including their scheduling and course associations.

    Attributes:
        code (str): Unique code identifier for the batch
        name (str): Name of the batch
        start_date (date): Start date of the batch
        end_date (date): End date of the batch
        course_id (int): Reference to the associated course
        active (bool): Batch active status
    """

    _name = "op.batch"
    _inherit = "mail.thread"
    _description = "OpenEduCat Batch"
    _order = "start_date"

    code = fields.Char(
        string='Code',
        size=16,
        required=True,
        tracking=True,
        help="Unique code identifier for the batch"
    )
    
    name = fields.Char(
        string='Name',
        size=32,
        required=True,
        tracking=True,
        help="Name of the batch"
    )
    
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today(),
        tracking=True,
        help="Start date of the batch"
    )
    
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True,
        help="End date of the batch"
    )
    
    course_id = fields.Many2one(
        comodel_name='op.course',
        string='Course',
        required=True,
        tracking=True,
        help="Course associated with the batch"
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True,
        help="Batch active status"
    )

    _sql_constraints = [
        ('unique_batch_code',
         'unique(code)',
         'Code should be unique per batch!')
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate batch dates.

        Ensures that:
        - End date is not before start date

        Raises:
            ValidationError: If date validation fails
        """
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(_(
                    "End Date cannot be set before Start Date."))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Search for batches by name.

        If context contains 'get_parent_batch', also includes batches
        from parent courses in the search results.

        Args:
            name (str): Name to search for
            args (list): Additional search criteria
            operator (str): Search operator
            limit (int): Maximum number of results

        Returns:
            list: List of (id, display_name) tuples
        """
        if self.env.context.get('get_parent_batch', False):
            course_ids = [self.env.context.get('course_id')]
            courses = self.env['op.course'].browse(course_ids)
            
            # Collect all parent course IDs
            while courses.parent_id:
                course_ids.append(courses.parent_id.id)
                courses = courses.parent_id
            
            # Search for batches in all related courses
            batches = self.search([('course_id', 'in', course_ids)])
            return [(batch.id, batch.display_name) for batch in batches]
            
        return super().name_search(name, args, operator=operator, limit=limit)

    @api.model
    def get_import_templates(self):
        """Get the import template for batch data.

        Returns:
            list: List containing template information
        """
        return [{
            'label': _('Import Template for Batch'),
            'template': '/openeducat_core/static/xls/op_batch.xls'
        }]
