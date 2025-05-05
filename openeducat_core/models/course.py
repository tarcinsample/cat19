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


class OpCourse(models.Model):
    """Course model for managing educational courses.

    This model represents courses that can be offered in educational institutions.
    It includes information about course name, code, evaluation type, and associated subjects.

    Attributes:
        name (str): Name of the course
        code (str): Unique code identifier for the course
        parent_id (int): Reference to parent course if this is a sub-course
        evaluation_type (str): Type of evaluation system used
        subject_ids (list): List of subjects associated with the course
        max_unit_load (float): Maximum unit load allowed
        min_unit_load (float): Minimum unit load required
        department_id (int): Department offering the course
        program_id (int): Program this course belongs to
        active (bool): Whether the course is active
    """

    _name = "op.course"
    _inherit = "mail.thread"
    _description = "OpenEduCat Course"
    _order = "name"

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        tracking=True,
        help="Name of the course"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=16,
        tracking=True,
        help="Unique code identifier for the course"
    )
    
    parent_id = fields.Many2one(
        comodel_name='op.course',
        string='Parent Course',
        tracking=True,
        help="Parent course if this is a sub-course"
    )
    
    evaluation_type = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('GPA', 'GPA'),
            ('CWA', 'CWA'),
            ('CCE', 'CCE')
        ],
        string='Evaluation Type',
        required=True,
        default="normal",
        tracking=True,
        help="Type of evaluation system used for the course"
    )
    
    subject_ids = fields.Many2many(
        comodel_name='op.subject',
        string='Subject(s)',
        help="Subjects associated with this course"
    )
    
    max_unit_load = fields.Float(
        string="Maximum Unit Load",
        tracking=True,
        help="Maximum unit load allowed for this course"
    )
    
    min_unit_load = fields.Float(
        string="Minimum Unit Load",
        tracking=True,
        help="Minimum unit load required for this course"
    )
    
    department_id = fields.Many2one(
        comodel_name='op.department',
        string='Department',
        tracking=True,
        default=lambda self: self.env.user.dept_id.id if self.env.user.dept_id else False,
        help="Department offering the course"
    )
    
    program_id = fields.Many2one(
        comodel_name='op.program',
        string="Program",
        tracking=True,
        help="Program this course belongs to"
    )
    
    active = fields.Boolean(
        default=True,
        help="If unchecked, the course will be hidden from the system"
    )

    _sql_constraints = [
        ('unique_course_code',
         'unique(code)',
         'Course code must be unique!')
    ]

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        """Check for recursive course hierarchy.

        Raises:
            ValidationError: If a recursive course hierarchy is detected.
        """
        if self._has_cycle():
            raise ValidationError(_('You cannot create recursive course hierarchy.'))

    @api.constrains('min_unit_load', 'max_unit_load')
    def _check_unit_load(self):
        """Validate that minimum unit load is not greater than maximum unit load.

        Raises:
            ValidationError: If minimum unit load is greater than maximum unit load.
        """
        for record in self:
            if record.min_unit_load and record.max_unit_load and \
               record.min_unit_load > record.max_unit_load:
                raise ValidationError(_('Minimum unit load cannot be greater than maximum unit load.'))

    @api.model
    def get_import_templates(self):
        """Get the import template for courses.

        Returns:
            List containing template information with label and template path.
        """
        return [{
            'label': _('Import Template for Courses'),
            'template': '/openeducat_core/static/xls/op_course.xls'
        }]
