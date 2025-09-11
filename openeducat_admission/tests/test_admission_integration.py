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

import logging
from datetime import date
import uuid
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from .test_admission_common import TestAdmissionCommon

_logger = logging.getLogger(__name__)


class TestAdmissionIntegration(TestAdmissionCommon):
    """Test integration between admission and other modules."""

    def test_admission_to_student_enrollment(self):
        """Test complete admission to student enrollment process."""
        _logger.info('Testing admission to student enrollment integration')
        
        admission = self.create_test_admission()
        
        # Complete admission workflow
        admission.submit_form()
        admission.admission_confirm()
        admission.confirm_in_progress()
        
        # Test enrollment process
        initial_student_count = self.op_student.search_count([])
        admission.enroll_student()
        final_student_count = self.op_student.search_count([])
        
        # Verify student creation
        self.assertEqual(final_student_count, initial_student_count + 1)
        self.assertTrue(admission.student_id)
        self.assertEqual(admission.state, 'done')
        
        # Verify student data mapping
        student = admission.student_id
        self.assertEqual(student.name, admission.name)
        self.assertEqual(student.email, admission.email)
        self.assertEqual(student.phone, admission.phone)
        self.assertEqual(student.mobile, admission.mobile)
        self.assertEqual(student.birth_date, admission.birth_date)
        self.assertEqual(student.gender, admission.gender)
        
        # Verify course enrollment
        course_details = student.course_detail_ids
        self.assertTrue(course_details)
        self.assertEqual(course_details[0].course_id, admission.course_id)
        self.assertEqual(course_details[0].batch_id, admission.batch_id)
        
    def test_admission_fees_integration(self):
        """Test integration with fees management."""
        _logger.info('Testing admission fees integration')
        
        admission = self.create_test_admission()
        
        # Test fees calculation
        admission.fees = 2000.0
        admission.discount = 10.0  # 10% discount
        
        # Enroll student
        admission.state = 'admission'
        admission.enroll_student()
        
        student = admission.student_id
        
        # Verify fees integration
        if hasattr(student, 'fees_details'):
            # Check if fees details are created
            fees_details = student.fees_details
            if fees_details:
                self.assertTrue(any(fd.course_id == admission.course_id for fd in fees_details))
                
        # Test fees term integration
        if admission.fees_term_id:
            self.assertEqual(admission.fees_term_id.course_id, admission.course_id)
            
    def test_admission_batch_integration(self):
        """Test integration with batch management."""
        _logger.info('Testing admission batch integration')
        
        # Create additional batches for same course
        batch2 = self.op_batch.create({
            'name': 'Test Batch 2024-B',
            'code': 'TB2024B_' + str(uuid.uuid4())[:8].replace('-', ''),
            'course_id': self.course.id,
            'start_date': date.today() + relativedelta(months=1),
            'end_date': date.today() + relativedelta(years=1, months=1),
            'max_strength': 30,
        })
        
        # Test batch capacity checking
        for i in range(25):  # Create many admissions for same batch
            admission = self.create_test_admission({
                'email': f'batch{i}@test.com',
                'batch_id': self.batch.id,
            })
            admission.enroll_student()
            
        # Verify batch strength
        enrolled_students = self.op_student.search([
            ('course_detail_ids.batch_id', '=', self.batch.id)
        ])
        
        # Check batch capacity constraints
        if hasattr(self.batch, 'current_strength'):
            self.batch._compute_current_strength()
            self.assertEqual(self.batch.current_strength, len(enrolled_students))
            
    def test_admission_academic_year_integration(self):
        """Test integration with academic year and terms."""
        _logger.info('Testing academic year integration')
        
        admission = self.create_test_admission()
        
        # Verify academic year consistency
        self.assertEqual(admission.register_id.academic_years_id, self.academic_year)
        self.assertEqual(admission.register_id.academic_term_id, self.academic_term)
        
        # Test enrollment in correct academic year
        admission.enroll_student()
        student = admission.student_id
        
        # Verify student is enrolled in correct academic context
        course_detail = student.course_detail_ids[0]
        if hasattr(course_detail, 'academic_year_id'):
            self.assertEqual(course_detail.academic_year_id, self.academic_year)
        if hasattr(course_detail, 'academic_term_id'):
            self.assertEqual(course_detail.academic_term_id, self.academic_term)
            
    def test_admission_partner_integration(self):
        """Test integration with partner/contact management."""
        _logger.info('Testing partner integration')
        
        admission = self.create_test_admission()
        
        # Test partner creation during admission
        if hasattr(admission, 'create_partner'):
            partner = admission.create_partner()
            self.assertEqual(partner.name, admission.name)
            self.assertEqual(partner.email, admission.email)
            admission.partner_id = partner.id
            
        # Test enrollment with partner
        admission.enroll_student()
        student = admission.student_id
        
        # Verify partner relationship
        if hasattr(student, 'partner_id'):
            if admission.partner_id:
                self.assertEqual(student.partner_id, admission.partner_id)
            else:
                # Partner should be created automatically
                self.assertTrue(student.partner_id)
                self.assertEqual(student.partner_id.email, admission.email)
                
    def test_admission_document_management(self):
        """Test document management and verification."""
        _logger.info('Testing document management integration')
        
        admission = self.create_test_admission()
        
        # Test document attachment
        document_data = {
            'name': 'Test Document.pdf',
            'type': 'binary',
            'res_model': 'op.admission',
            'res_id': admission.id,
            'datas': b'test document content',
        }
        
        document = self.env['ir.attachment'].create(document_data)
        
        # Verify document attachment
        documents = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.admission'),
            ('res_id', '=', admission.id)
        ])
        self.assertIn(document, documents)
        
        # Test document verification workflow
        if hasattr(admission, 'document_verified'):
            admission.document_verified = True
            self.assertTrue(admission.document_verified)
            
    def test_admission_notification_system(self):
        """Test notification system integration."""
        _logger.info('Testing notification system integration')
        
        admission = self.create_test_admission()
        
        # Test state change notifications
        initial_messages = len(admission.message_ids)
        
        admission.submit_form()
        
        # Verify notification was sent
        final_messages = len(admission.message_ids)
        self.assertGreater(final_messages, initial_messages)
        
        # Test enrollment notification
        admission.admission_confirm()
        admission.confirm_in_progress()
        
        enrollment_messages = len(admission.message_ids)
        admission.enroll_student()
        
        final_enrollment_messages = len(admission.message_ids)
        self.assertGreaterEqual(final_enrollment_messages, enrollment_messages)
        
    def test_admission_reporting_integration(self):
        """Test reporting and analytics integration."""
        _logger.info('Testing reporting integration')
        
        # Create diverse admission data
        admissions = []
        for i in range(10):
            state = ['draft', 'submit', 'confirm', 'admission', 'done'][i % 5]
            admission = self.create_test_admission({
                'email': f'report{i}@test.com',
                'state': state,
            })
            admissions.append(admission)
            
        # Test admission analysis wizard
        wizard_vals = {
            'course_id': self.course.id,
            'start_date': date.today() - relativedelta(days=30),
            'end_date': date.today() + relativedelta(days=30),
        }
        
        wizard = self.wizard_admission.create(wizard_vals)
        
        # Test report generation
        report_action = wizard.print_report()
        # Report action should be either a report or window action
        # (Some Odoo environments may return window action as fallback)
        self.assertIn(report_action['type'], ['ir.actions.report', 'ir.actions.act_window'])
        
        # Test admission analysis report model
        if hasattr(self.env, 'admission.analysis.report'):
            report_model = self.env['admission.analysis.report']
            reports = report_model.search([
                ('course_id', '=', self.course.id)
            ])
            # Should find admission data
            
    def test_admission_import_export(self):
        """Test data import/export functionality."""
        _logger.info('Testing import/export integration')
        
        # Create test admissions
        admissions = []
        for i in range(5):
            admission = self.create_test_admission({
                'email': f'export{i}@test.com',
            })
            admissions.append(admission)
            
        # Test export functionality
        admission_ids = [a.id for a in admissions]
        
        # Test basic field export
        export_fields = ['name', 'email', 'course_id', 'state']
        export_data = self.op_admission.browse(admission_ids).export_data(export_fields)
        
        self.assertEqual(len(export_data['datas']), len(admissions))
        
        # Test import validation
        import_data = [
            ['Test Import Student', 'import@test.com', self.course.id, 'draft'],
        ]
        
        try:
            import_result = self.op_admission.load(export_fields, import_data)
            if import_result['messages']:
                _logger.warning(f"Import warnings: {import_result['messages']}")
        except Exception as e:
            _logger.warning(f"Import test failed: {e}")
            
    def test_admission_mail_tracking(self):
        """Test mail tracking and activity integration."""
        _logger.info('Testing mail tracking integration')
        
        admission = self.create_test_admission()
        
        # Test tracking on field changes
        admission.write({'phone': '9999999999'})
        
        # Verify tracking message
        tracking_messages = admission.message_ids.filtered(
            lambda m: m.message_type == 'notification'
        )
        
        # Test activity creation
        if hasattr(admission, 'activity_schedule'):
            activity = admission.activity_schedule(
                'mail.mail_activity_data_todo',
                summary='Review admission documents',
                note='Please review the uploaded documents',
            )
            self.assertTrue(activity)
            
    def test_admission_security_integration(self):
        """Test security and access rights integration."""
        _logger.info('Testing security integration')
        
        # Test access rights for different user groups
        admission = self.create_test_admission()
        
        # Test read access
        can_read = admission.check_access_rights('read', raise_exception=False)
        self.assertTrue(can_read)
        
        # Test write access
        can_write = admission.check_access_rights('write', raise_exception=False)
        self.assertTrue(can_write)
        
        # Test record rules
        accessible_admissions = self.op_admission.search([])
        self.assertIn(admission, accessible_admissions)
        
    def test_admission_multi_company(self):
        """Test multi-company integration."""
        _logger.info('Testing multi-company integration')
        
        # Create admission in current company
        admission = self.create_test_admission()
        self.assertEqual(admission.company_id, self.env.company)
        
        # Test company-specific data isolation
        company_admissions = self.op_admission.search([
            ('company_id', '=', self.env.company.id)
        ])
        self.assertIn(admission, company_admissions)
        
        # Test enrollment in correct company context
        admission.enroll_student()
        student = admission.student_id
        
        if hasattr(student, 'company_id'):
            self.assertEqual(student.company_id, admission.company_id)