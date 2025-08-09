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


class FeesDetailReportWizard(models.TransientModel):
    """Fees Detail Report Wizard
    
    This wizard generates fee reports filtered by student or course,
    providing detailed analysis of fee payments and pending amounts.
    """
    _name = "fees.detail.report.wizard"
    _description = "Wizard For Fees Details Report"

    fees_filter = fields.Selection(
        [('student', 'Student'), ('course', 'Course')],
        'Fees Filter', required=True,
        help="Choose filter type for fees report")
    student_id = fields.Many2one(
        'op.student', 'Student',
        help="Select student for detailed fee report")
    course_id = fields.Many2one(
        'op.course', 'Course',
        help="Select course for fee analysis")

    @api.constrains('fees_filter', 'student_id', 'course_id')
    def _check_filter_selection(self):
        """Validate filter selection."""
        for wizard in self:
            if wizard.fees_filter == 'student' and not wizard.student_id:
                raise ValidationError(
                    _("Please select a student for student-based report."))
            elif wizard.fees_filter == 'course' and not wizard.course_id:
                raise ValidationError(
                    _("Please select a course for course-based report."))
    
    def print_report(self):
        """Generate fees detail report based on selected filter.
        
        Returns:
            dict: Report action with appropriate data context
        """
        self.ensure_one()
        
        data = {
            'fees_filter': self.fees_filter,
            'wizard_id': self.id
        }
        
        if self.fees_filter == 'student':
            if not self.student_id:
                raise ValidationError(
                    _("Please select a student for the report."))
            data['student'] = self.student_id.id
            data['student_name'] = self.student_id.name
        else:
            if not self.course_id:
                raise ValidationError(
                    _("Please select a course for the report."))
            data['course'] = self.course_id.id
            data['course_name'] = self.course_id.name

        report = self.env.ref(
            'openeducat_fees.action_report_fees_detail_analysis')
        return report.report_action(self, data=data)
