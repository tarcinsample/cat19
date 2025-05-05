# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    OpenEduCat Inc
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<https://www.openeducat.org>).
#
##############################################################################

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpAcademicYear(models.Model):
    """Academic Year model for OpenEduCat.

    This model manages academic years within the institution,
    including their term structures and scheduling.

    Attributes:
        name (str): Name of the academic year
        start_date (date): Start date of the academic year
        end_date (date): End date of the academic year
        term_structure (str): Type of term structure for the year
        academic_term_ids (list): List of academic terms in the year
        create_boolean (bool): Flag for term creation status
        company_id (int): Reference to the company
    """

    _name = 'op.academic.year'
    _description = "Academic Year"
    _inherit = "mail.thread"
    _order = "start_date"

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Name of the academic year"
    )
    
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        help="Start date of the academic year"
    )
    
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True,
        help="End date of the academic year"
    )

    term_structure = fields.Selection([
        ('two_sem', 'Two Semesters'),
        ('two_sem_qua', 'Two Semesters subdivided by Quarters'),
        ('two_sem_final', 'Two Semesters subdivided by Quarters and Final Exams'),
        ('three_sem', 'Three Trimesters'),
        ('four_Quarter', 'Four Quarters'),
        ('final_year', 'Final Year Grades subdivided by Quarters'),
        ('others', 'Other(overlapping terms, custom schedules)')
    ], string='Term Structure',
        default='two_sem',
        required=True,
        tracking=True,
        help="Structure of terms within the academic year"
    )
    
    academic_term_ids = fields.One2many(
        comodel_name='op.academic.term',
        inverse_name='academic_year_id',
        string='Academic Terms',
        tracking=True
    )
    
    create_boolean = fields.Boolean(
        string='Terms Created',
        tracking=True,
        help="Indicates if terms have been created for this academic year"
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        tracking=True
    )

    _sql_constraints = [
        ('unique_year_name',
         'unique(name)',
         'Academic year name must be unique!')
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate academic year dates.

        Ensures that:
        - End date is not before start date
        - Academic year dates don't overlap with other years

        Raises:
            ValidationError: If any date validation fails
        """
        for record in self:
            if record.end_date < record.start_date:
                raise ValidationError(_(
                    "End date cannot be earlier than start date!"))

            # Check for overlapping years
            overlapping = self.search([
                ('id', '!=', record.id),
                '|',
                '&',
                ('start_date', '<=', record.start_date),
                ('end_date', '>=', record.start_date),
                '&',
                ('start_date', '<=', record.end_date),
                ('end_date', '>=', record.end_date)
            ])
            if overlapping:
                raise ValidationError(_(
                    "Academic year dates cannot overlap with existing years!"))

    def _create_two_semester_terms(self):
        """Create two semester terms for the academic year."""
        if not self.academic_term_ids:
            from_d = self.start_date
            to_d = self.end_date
            delta = to_d - from_d
            day = (delta.days + 1) / 2

            terms = [
                {
                    'name': 'Semester 1',
                    'term_start_date': from_d,
                    'term_end_date': from_d + timedelta(days=day)
                },
                {
                    'name': 'Semester 2',
                    'term_start_date': from_d + timedelta(days=day + 1),
                    'term_end_date': to_d
                }
            ]

            for term in terms:
                self.env['op.academic.term'].create({
                    **term,
                    'academic_year_id': self.id
                })

    def _create_quarter_terms(self, parent_term, quarter_num):
        """Create quarter terms for a parent term.

        Args:
            parent_term (op.academic.term): Parent term to create quarters for
            quarter_num (int): Starting quarter number
        """
        sub_from_d = parent_term.term_start_date
        sub_to_d = parent_term.term_end_date
        delta = sub_to_d - sub_from_d
        day = (delta.days + 1) / 2

        quarters = [
            {
                'name': f'Quarter {quarter_num}',
                'term_start_date': sub_from_d,
                'term_end_date': sub_from_d + timedelta(days=day)
            },
            {
                'name': f'Quarter {quarter_num + 1}',
                'term_start_date': sub_from_d + timedelta(days=day + 1),
                'term_end_date': sub_to_d
            }
        ]

        for quarter in quarters:
            self.env['op.academic.term'].create({
                **quarter,
                'academic_year_id': self.id,
                'parent_term': parent_term.id
            })

    def _create_final_exam_term(self, parent_term, exam_num):
        """Create final exam term for a parent term.

        Args:
            parent_term (op.academic.term): Parent term to create exam for
            exam_num (int): Exam number
        """
        self.env['op.academic.term'].create({
            'name': f'Final Exam {exam_num}',
            'term_start_date': parent_term.term_end_date,
            'term_end_date': parent_term.term_end_date,
            'academic_year_id': self.id,
            'parent_term': parent_term.id
        })

    def _create_three_semester_terms(self):
        """Create three semester terms for the academic year."""
        if not self.academic_term_ids:
            from_d = self.start_date
            to_d = self.end_date
            delta = to_d - from_d
            day = (delta.days + 1) / 3

            terms = [
                {
                    'name': 'Semester 1',
                    'term_start_date': from_d,
                    'term_end_date': from_d + timedelta(days=day)
                },
                {
                    'name': 'Semester 2',
                    'term_start_date': from_d + timedelta(days=day + 1),
                    'term_end_date': from_d + timedelta(days=2 * day)
                },
                {
                    'name': 'Semester 3',
                    'term_start_date': from_d + timedelta(days=2 * day + 1),
                    'term_end_date': to_d
                }
            ]

            for term in terms:
                self.env['op.academic.term'].create({
                    **term,
                    'academic_year_id': self.id
                })

    def _create_four_quarter_terms(self):
        """Create four quarter terms for the academic year."""
        if not self.academic_term_ids:
            from_d = self.start_date
            to_d = self.end_date
            delta = to_d - from_d
            day = (delta.days + 1) / 4

            terms = [
                {
                    'name': 'Quarter 1',
                    'term_start_date': from_d,
                    'term_end_date': from_d + timedelta(days=day)
                },
                {
                    'name': 'Quarter 2',
                    'term_start_date': from_d + timedelta(days=day + 1),
                    'term_end_date': from_d + timedelta(days=2 * day)
                },
                {
                    'name': 'Quarter 3',
                    'term_start_date': from_d + timedelta(days=2 * day + 1),
                    'term_end_date': from_d + timedelta(days=3 * day)
                },
                {
                    'name': 'Quarter 4',
                    'term_start_date': from_d + timedelta(days=3 * day + 1),
                    'term_end_date': to_d
                }
            ]

            for term in terms:
                self.env['op.academic.term'].create({
                    **term,
                    'academic_year_id': self.id
                })

    def term_create(self):
        """Create terms based on the selected term structure.

        Creates appropriate terms and sub-terms based on the
        term_structure field value.
        """
        self.create_boolean = True
        academic_terms = self.env['op.academic.term']

        if self.term_structure == 'two_sem':
            self._create_two_semester_terms()

        elif self.term_structure == 'two_sem_qua':
            self._create_two_semester_terms()
            quarter_num = 1
            for term in self.academic_term_ids:
                self._create_quarter_terms(term, quarter_num)
                quarter_num += 2

        elif self.term_structure == 'two_sem_final':
            self._create_two_semester_terms()
            quarter_num = 1
            exam_num = 1
            for term in self.academic_term_ids:
                self._create_quarter_terms(term, quarter_num)
                self._create_final_exam_term(term, exam_num)
                quarter_num += 2
                exam_num += 1

        elif self.term_structure == 'three_sem':
            self._create_three_semester_terms()

        elif self.term_structure == 'four_Quarter':
            self._create_four_quarter_terms()
