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


class OpResultTemplate(models.Model):
    _name = "op.result.template"
    _inherit = ["mail.thread"]
    _description = "Result Template"

    exam_session_id = fields.Many2one(
        'op.exam.session', 'Exam Session',
        required=True, tracking=True)
    evaluation_type = fields.Selection(
        related='exam_session_id.evaluation_type',
        store=True, tracking=True)
    name = fields.Char("Name", size=254,
                       required=True, tracking=True)
    result_date = fields.Date(
        'Result Date', required=True,
        default=fields.Date.today(), tracking=True)
    grade_ids = fields.Many2many(
        'op.grade.configuration', string='Grade Configuration')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('result_generated', 'Result Generated')
    ], string='State', default='draft', tracking=True)
    active = fields.Boolean(default=True)

    @api.constrains('exam_session_id')
    def _check_exam_session(self):
        for record in self:
            for exam in record.exam_session_id.exam_ids:
                if exam.state != 'done':
                    raise ValidationError(
                        _('All subject exam should be done.'))

    @api.constrains('grade_ids')
    def _check_min_max_per(self):
        for record in self:
            count = 0
            for grade in record.grade_ids:
                for sub_grade in record.grade_ids:
                    if grade != sub_grade:
                        if (sub_grade.min_per <= grade.min_per and
                            sub_grade.max_per >= grade.min_per) or \
                                (sub_grade.min_per <= grade.max_per and
                                 sub_grade.max_per >= grade.max_per):
                            count += 1
            if count > 0:
                raise ValidationError(
                    _('Percentage range conflict with other record.'))

    def generate_result(self):
        """Generate result marksheets for exam session.
        
        Creates marksheet register and lines for all students with optimized batch operations.
        """
        for record in self:
            # Validate exam session has completed exams
            if not record.exam_session_id.exam_ids:
                raise ValidationError(_(
                    "Cannot generate results for session without exams."))
                    
            incomplete_exams = record.exam_session_id.exam_ids.filtered(
                lambda e: e.state not in ['held', 'result_updated', 'done'])
            if incomplete_exams:
                exam_names = ', '.join(incomplete_exams.mapped('name'))
                raise ValidationError(_(
                    "Cannot generate results. The following exams are not completed: %s") % 
                    exam_names)
            
            # Create marksheet register
            marksheet_reg_id = self.env['op.marksheet.register'].create({
                'name': f"Mark Sheet for {record.exam_session_id.name}",
                'exam_session_id': record.exam_session_id.id,
                'generated_date': fields.Date.today(),
                'generated_by': self.env.uid,
                'state': 'draft',
                'result_template_id': record.id
            })
            
            # Collect student data efficiently
            student_dict = {}
            result_lines_data = []
            
            for exam in record.exam_session_id.exam_ids:
                for attendee in exam.attendees_line:
                    # Prepare result line data for batch creation
                    result_lines_data.append({
                        'student_id': attendee.student_id.id,
                        'exam_id': exam.id,
                        'marks': str(attendee.marks if attendee.marks is not None else 0),
                    })
                    
                    # Track students for marksheet line creation
                    if attendee.student_id.id not in student_dict:
                        student_dict[attendee.student_id.id] = []
                    student_dict[attendee.student_id.id].append(len(result_lines_data) - 1)
            
            # Batch create result lines
            result_lines = self.env['op.result.line'].create(result_lines_data)
            
            # Create marksheet lines and link result lines
            marksheet_lines_data = []
            for student_id in student_dict:
                marksheet_lines_data.append({
                    'student_id': student_id,
                    'marksheet_reg_id': marksheet_reg_id.id,
                })
            
            # Batch create marksheet lines
            marksheet_lines = self.env['op.marksheet.line'].create(marksheet_lines_data)
            
            # Link result lines to marksheet lines
            for i, (student_id, result_indices) in enumerate(student_dict.items()):
                marksheet_line = marksheet_lines[i]
                for result_index in result_indices:
                    result_lines[result_index].marksheet_line_id = marksheet_line.id
            
            record.state = 'result_generated'
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Generated Marksheet Register'),
                'res_model': 'op.marksheet.register',
                'res_id': marksheet_reg_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
