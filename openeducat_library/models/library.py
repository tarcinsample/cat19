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


class OpLibraryCardType(models.Model):
    _name = "op.library.card.type"
    _description = "Library Card Type"

    name = fields.Char('Name', size=256, required=True)
    allow_media = fields.Integer('No Of Medias Allowed', default=10,
                                 required=True)
    duration = fields.Integer(
        'Duration', help='Duration in terms of Number of Lead Days',
        required=True)
    penalty_amt_per_day = fields.Float('Penalty Amount Per Day',
                                       required=True)

    @api.constrains('allow_media', 'duration', 'penalty_amt_per_day')
    def _check_card_type_details(self):
        """Validate library card type configuration.
        
        Raises:
            ValidationError: If card type values are invalid
        """
        for record in self:
            if record.allow_media < 0:
                raise ValidationError(_(
                    "Number of allowed media cannot be negative."))
            if record.duration <= 0:
                raise ValidationError(_(
                    "Duration must be positive (minimum 1 day)."))
            if record.penalty_amt_per_day < 0:
                raise ValidationError(_(
                    "Penalty amount per day cannot be negative."))


class OpLibraryCard(models.Model):
    _name = "op.library.card"
    _rec_name = "number"
    _description = "Library Card"

    partner_id = fields.Many2one(
        'res.partner', 'Student/Faculty', required=True)
    number = fields.Char('Number', size=256, readonly=True)
    library_card_type_id = fields.Many2one(
        'op.library.card.type', 'Card Type', required=True)
    issue_date = fields.Date(
        'Issue Date', required=True, default=fields.Date.today())
    type = fields.Selection(
        [('student', 'Student'), ('faculty', 'Faculty')],
        'Type', default='student', required=True)
    student_id = fields.Many2one('op.student', 'Student',
                                 domain=[('library_card_id', '=', False)])
    faculty_id = fields.Many2one('op.faculty', 'Faculty',
                                 domain=[('library_card_id', '=', False)])
    active = fields.Boolean(default=True)

    _sql_constraints = [(
        'unique_library_card_number',
        'unique(number)',
        'Library card Number should be unique per card!')]

    @api.constrains('student_id', 'faculty_id', 'type')
    def _check_student_faculty_consistency(self):
        """Validate student/faculty consistency with card type.
        
        Raises:
            ValidationError: If type doesn't match selected person
        """
        for record in self:
            if record.type == 'student' and not record.student_id:
                raise ValidationError(_(
                    "Student must be selected for student library card."))
            if record.type == 'faculty' and not record.faculty_id:
                raise ValidationError(_(
                    "Faculty must be selected for faculty library card."))
            if record.type == 'student' and record.faculty_id:
                raise ValidationError(_(
                    "Faculty cannot be selected for student library card."))
            if record.type == 'faculty' and record.student_id:
                raise ValidationError(_(
                    "Student cannot be selected for faculty library card."))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate card number and link to student/faculty.
        
        Ensures proper sequence generation and establishes bidirectional links.
        """
        for vals in vals_list:
            sequence = self.env['ir.sequence'].next_by_code('op.library.card')
            if not sequence:
                raise ValidationError(_(
                    "Unable to generate library card number. "
                    "Please check sequence configuration."))
            vals['number'] = sequence
            
        result = super(OpLibraryCard, self).create(vals_list)
        
        # Link cards to students/faculty
        for res in result:
            if res.type == 'student' and res.student_id:
                res.student_id.library_card_id = res.id
            elif res.type == 'faculty' and res.faculty_id:
                res.faculty_id.library_card_id = res.id
                
        return result

    @api.onchange('type')
    def onchange_type(self):
        """Clear person fields when card type changes."""
        self.student_id = False
        self.faculty_id = False
        self.partner_id = False
        
        # Return domain based on card type
        if self.type == 'student':
            return {
                'domain': {
                    'student_id': [('library_card_id', '=', False), ('active', '=', True)]
                }
            }
        elif self.type == 'faculty':
            return {
                'domain': {
                    'faculty_id': [('library_card_id', '=', False), ('active', '=', True)]
                }
            }

    @api.onchange('student_id', 'faculty_id')
    def onchange_student_faculty(self):
        """Update partner when student or faculty is selected."""
        if self.student_id:
            self.partner_id = self.student_id.partner_id
            # Ensure consistency with card type
            if self.type != 'student':
                self.type = 'student'
        elif self.faculty_id:
            self.partner_id = self.faculty_id.partner_id
            # Ensure consistency with card type
            if self.type != 'faculty':
                self.type = 'faculty'
        else:
            self.partner_id = False
            
    def get_issued_media_count(self):
        """Get count of currently issued media for this card.
        
        Returns number of media units currently issued to this card.
        """
        self.ensure_one()
        return self.env['op.media.movement'].search_count([
            ('library_card_id', '=', self.id),
            ('state', '=', 'issue')
        ])
        
    def check_media_limit(self):
        """Check if card has reached media limit.
        
        Returns True if more media can be issued, False otherwise.
        """
        self.ensure_one()
        current_count = self.get_issued_media_count()
        return current_count < self.library_card_type_id.allow_media
        
    def get_overdue_media(self):
        """Get list of overdue media for this card.
        
        Returns recordset of overdue media movements.
        """
        self.ensure_one()
        today = fields.Date.today()
        return self.env['op.media.movement'].search([
            ('library_card_id', '=', self.id),
            ('state', '=', 'issue'),
            ('return_date', '<', today)
        ])
