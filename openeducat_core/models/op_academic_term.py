# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<https://www.openeducat.org>).
#
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpAcademicTerm(models.Model):
    """Academic Term model for OpenEduCat.

    This model manages academic terms within the institution,
    including their scheduling and hierarchical relationships.

    Attributes:
        name (str): Name of the academic term
        term_start_date (date): Start date of the term
        term_end_date (date): End date of the term
        academic_year_id (int): Reference to the academic year
        parent_term (int): Reference to parent term for hierarchical structure
        company_id (int): Reference to the company
    """

    _name = 'op.academic.term'
    _description = "Academic Term"
    _inherit = "mail.thread"
    _order = "term_start_date"

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Name of the academic term"
    )
    
    term_start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        help="Start date of the academic term"
    )
    
    term_end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True,
        help="End date of the academic term"
    )
    
    academic_year_id = fields.Many2one(
        comodel_name='op.academic.year',
        string='Academic Year',
        required=True,
        tracking=True,
        help="Academic year this term belongs to"
    )
    
    parent_term = fields.Many2one(
        comodel_name='op.academic.term',
        string='Parent Term',
        tracking=True,
        help="Parent term in the hierarchical structure"
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        tracking=True
    )

    _sql_constraints = [
        ('unique_term_name',
         'unique(name, academic_year_id)',
         'Term name must be unique within an academic year!')
    ]

    @api.constrains('term_start_date', 'term_end_date')
    def _check_dates(self):
        """Validate term dates.

        Ensures that:
        - End date is not before start date
        - Term dates fall within the academic year
        - Term dates don't overlap with other terms

        Raises:
            ValidationError: If any date validation fails
        """
        for record in self:
            if record.term_end_date < record.term_start_date:
                raise ValidationError(_(
                    "End date cannot be earlier than start date!"))

            if record.academic_year_id:
                if (record.term_start_date < record.academic_year_id.start_date or
                        record.term_end_date > record.academic_year_id.end_date):
                    raise ValidationError(_(
                        "Term dates must fall within the academic year!"))

            # Check for overlapping terms
            overlapping = self.search([
                ('id', '!=', record.id),
                ('academic_year_id', '=', record.academic_year_id.id),
                '|',
                '&',
                ('term_start_date', '<=', record.term_start_date),
                ('term_end_date', '>=', record.term_start_date),
                '&',
                ('term_start_date', '<=', record.term_end_date),
                ('term_end_date', '>=', record.term_end_date)
            ])
            if overlapping:
                raise ValidationError(_(
                    "Term dates cannot overlap with existing terms!"))
