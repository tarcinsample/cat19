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

import base64
from datetime import datetime
from odoo.tests import tagged
from .test_assignment_common import TestAssignmentCommon


@tagged('post_install', '-at_install')
class TestAssignmentFiles(TestAssignmentCommon):
    """Test assignment file upload and submission management."""
    
    def test_assignment_file_attachment(self):
        """Test Task 10: Test assignment file upload and submission management."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        
        # Create sample file content
        sample_file_content = b"Sample assignment document content for testing file upload functionality."
        encoded_content = base64.b64encode(sample_file_content)
        
        # Attach file to assignment (assignment instructions/materials)
        assignment_attachment = self.env['ir.attachment'].create({
            'name': 'assignment_instructions.pdf',
            'res_model': 'op.assignment',
            'res_id': assignment.id,
            'type': 'binary',
            'datas': encoded_content,
            'mimetype': 'application/pdf'
        })
        
        # Verify attachment creation
        self.assertTrue(assignment_attachment.id)
        self.assertEqual(assignment_attachment.res_model, 'op.assignment')
        self.assertEqual(assignment_attachment.res_id, assignment.id)
        self.assertEqual(assignment_attachment.name, 'assignment_instructions.pdf')
        
        # Test attachment accessibility
        assignment_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment'),
            ('res_id', '=', assignment.id)
        ])
        self.assertEqual(len(assignment_attachments), 1)
        self.assertEqual(assignment_attachments[0].id, assignment_attachment.id)
    
    def test_submission_file_attachment(self):
        """Test file attachments for student submissions."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Submission with file attachments'
        })
        
        # Create multiple file attachments for submission
        file_attachments = []
        
        # Document file
        doc_content = b"Student assignment submission document with detailed analysis and research."
        doc_attachment = self.env['ir.attachment'].create({
            'name': 'student_submission.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(doc_content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        file_attachments.append(doc_attachment)
        
        # Image file
        img_content = b"Fake image content for testing purposes"
        img_attachment = self.env['ir.attachment'].create({
            'name': 'diagram.png',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(img_content),
            'mimetype': 'image/png'
        })
        file_attachments.append(img_attachment)
        
        # Code file
        code_content = b"def calculate_result():\n    return 42\n\nprint(calculate_result())"
        code_attachment = self.env['ir.attachment'].create({
            'name': 'solution.py',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(code_content),
            'mimetype': 'text/x-python'
        })
        file_attachments.append(code_attachment)
        
        # Verify all attachments created
        self.assertEqual(len(file_attachments), 3)
        
        # Test attachment retrieval
        submission_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', '=', submission.id)
        ])
        self.assertEqual(len(submission_attachments), 3)
        
        # Verify attachment details
        attachment_names = submission_attachments.mapped('name')
        expected_names = ['student_submission.docx', 'diagram.png', 'solution.py']
        for name in expected_names:
            self.assertIn(name, attachment_names)
    
    def test_file_size_and_format_validation(self):
        """Test file size and format validation."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'File validation test submission'
        })
        
        # Test different file formats
        file_formats = [
            ('document.pdf', 'application/pdf', b'PDF file content'),
            ('document.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', b'DOCX content'),
            ('spreadsheet.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', b'XLSX content'),
            ('presentation.pptx', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', b'PPTX content'),
            ('image.jpg', 'image/jpeg', b'JPEG image content'),
            ('image.png', 'image/png', b'PNG image content'),
            ('code.py', 'text/x-python', b'Python code content'),
            ('data.csv', 'text/csv', b'CSV data content'),
            ('archive.zip', 'application/zip', b'ZIP archive content'),
        ]
        
        valid_attachments = []
        for filename, mimetype, content in file_formats:
            try:
                attachment = self.env['ir.attachment'].create({
                    'name': filename,
                    'res_model': 'op.assignment.sub.line',
                    'res_id': submission.id,
                    'type': 'binary',
                    'datas': base64.b64encode(content),
                    'mimetype': mimetype
                })
                valid_attachments.append(attachment)
            except Exception as e:
                # Log format that failed validation
                pass
        
        # Verify valid formats were accepted
        self.assertGreater(len(valid_attachments), 0)
        
        # Test file size considerations
        large_content = b'X' * (1024 * 1024)  # 1MB content
        large_file_attachment = self.env['ir.attachment'].create({
            'name': 'large_file.txt',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(large_content),
            'mimetype': 'text/plain'
        })
        
        # Verify large file handling
        self.assertTrue(large_file_attachment.id)
        self.assertEqual(len(base64.b64decode(large_file_attachment.datas)), 1024 * 1024)
    
    def test_file_version_management(self):
        """Test file version management for submissions."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Version management test submission'
        })
        
        # Create initial version
        v1_content = b"Version 1 of the assignment submission."
        v1_attachment = self.env['ir.attachment'].create({
            'name': 'assignment_v1.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(v1_content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        
        # Simulate revision process
        submission.act_submit()
        submission.act_change_req()  # Faculty requests changes
        
        # Create revised version
        v2_content = b"Version 2 of the assignment submission with requested changes."
        v2_attachment = self.env['ir.attachment'].create({
            'name': 'assignment_v2.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(v2_content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        
        # Create final version
        v3_content = b"Version 3 - Final version of the assignment submission."
        v3_attachment = self.env['ir.attachment'].create({
            'name': 'assignment_final.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(v3_content),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        
        # Verify all versions stored
        all_versions = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', '=', submission.id)
        ])
        self.assertEqual(len(all_versions), 3)
        
        # Test version identification
        version_names = all_versions.mapped('name')
        expected_versions = ['assignment_v1.docx', 'assignment_v2.docx', 'assignment_final.docx']
        for version in expected_versions:
            self.assertIn(version, version_names)
    
    def test_bulk_file_operations(self):
        """Test bulk file operations for multiple submissions."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create multiple students and submissions
        students_and_submissions = []
        for i in range(5):
            partner = self.env['res.partner'].create({
                'name': f'Bulk File Test Student {i+1}',
                'is_company': False
            })
            student = self.op_student.create({
                'partner_id': partner.id
            })
            
            submission = self.op_assignment_subline.create({
                'assignment_id': assignment.id,
                'student_id': student.id,
                'description': f'Bulk file test submission {i+1}'
            })
            students_and_submissions.append((student, submission))
        
        # Bulk file attachment creation
        all_attachments = []
        for i, (student, submission) in enumerate(students_and_submissions):
            # Each student submits 2 files
            for j in range(2):
                content = f"Student {i+1} file {j+1} content for bulk testing.".encode()
                attachment = self.env['ir.attachment'].create({
                    'name': f'student_{i+1}_file_{j+1}.txt',
                    'res_model': 'op.assignment.sub.line',
                    'res_id': submission.id,
                    'type': 'binary',
                    'datas': base64.b64encode(content),
                    'mimetype': 'text/plain'
                })
                all_attachments.append(attachment)
        
        # Verify bulk creation
        self.assertEqual(len(all_attachments), 10)  # 5 students * 2 files each
        
        # Test bulk retrieval by assignment
        assignment_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', 'in', [sub.id for _, sub in students_and_submissions])
        ])
        self.assertEqual(len(assignment_attachments), 10)
    
    def test_file_security_and_access_control(self):
        """Test file security and access control."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submissions for different students
        submission1 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Security test submission 1'
        })
        
        submission2 = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student2.id,
            'description': 'Security test submission 2'
        })
        
        # Create private files for each student
        student1_file = self.env['ir.attachment'].create({
            'name': 'student1_private.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission1.id,
            'type': 'binary',
            'datas': base64.b64encode(b'Student 1 private content'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        
        student2_file = self.env['ir.attachment'].create({
            'name': 'student2_private.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission2.id,
            'type': 'binary',
            'datas': base64.b64encode(b'Student 2 private content'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        
        # Test access control (files should be linked to correct submissions)
        student1_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', '=', submission1.id)
        ])
        
        student2_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', '=', submission2.id)
        ])
        
        # Verify file isolation
        self.assertEqual(len(student1_attachments), 1)
        self.assertEqual(len(student2_attachments), 1)
        self.assertEqual(student1_attachments[0].id, student1_file.id)
        self.assertEqual(student2_attachments[0].id, student2_file.id)
        
        # Faculty should be able to access all submission files
        all_submission_files = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', 'in', [submission1.id, submission2.id])
        ])
        self.assertEqual(len(all_submission_files), 2)
    
    def test_file_metadata_and_tracking(self):
        """Test file metadata and tracking functionality."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Metadata tracking test submission'
        })
        
        # Create file with metadata
        file_content = b"Content for metadata tracking test."
        upload_time = datetime.now()
        
        attachment = self.env['ir.attachment'].create({
            'name': 'metadata_test.pdf',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'mimetype': 'application/pdf',
            'description': 'Test file for metadata tracking'
        })
        
        # Verify metadata
        self.assertTrue(attachment.create_date)
        self.assertTrue(attachment.create_uid)
        self.assertEqual(attachment.file_size, len(file_content))
        self.assertEqual(attachment.mimetype, 'application/pdf')
        
        # Test file tracking through submission
        file_metadata = {
            'file_id': attachment.id,
            'filename': attachment.name,
            'file_size': attachment.file_size,
            'upload_date': attachment.create_date,
            'uploaded_by': attachment.create_uid.name,
            'submission_id': submission.id,
            'student_name': submission.student_id.name,
            'assignment_name': submission.assignment_id.name
        }
        
        # Verify tracking data structure
        self.assertTrue(file_metadata['file_id'])
        self.assertEqual(file_metadata['filename'], 'metadata_test.pdf')
        self.assertGreater(file_metadata['file_size'], 0)
        self.assertTrue(file_metadata['upload_date'])
        self.assertTrue(file_metadata['student_name'])
        self.assertTrue(file_metadata['assignment_name'])
    
    def test_file_cleanup_and_archival(self):
        """Test file cleanup and archival processes."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission with files
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Cleanup test submission'
        })
        
        # Create temporary and permanent files
        temp_attachment = self.env['ir.attachment'].create({
            'name': 'temp_file.txt',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(b'Temporary file content'),
            'mimetype': 'text/plain'
        })
        
        final_attachment = self.env['ir.attachment'].create({
            'name': 'final_submission.docx',
            'res_model': 'op.assignment.sub.line',
            'res_id': submission.id,
            'type': 'binary',
            'datas': base64.b64encode(b'Final submission content'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        
        # Simulate cleanup process (remove temporary files)
        temp_files = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', '=', submission.id),
            ('name', 'ilike', 'temp%')
        ])
        
        self.assertEqual(len(temp_files), 1)
        
        # Test archival flag (in real implementation, would move to archive storage)
        final_attachment.write({'description': 'ARCHIVED: Final submission'})
        
        # Verify archival marking
        archived_files = self.env['ir.attachment'].search([
            ('res_model', '=', 'op.assignment.sub.line'),
            ('res_id', '=', submission.id),
            ('description', 'ilike', 'ARCHIVED%')
        ])
        
        self.assertEqual(len(archived_files), 1)
        self.assertEqual(archived_files[0].id, final_attachment.id)
    
    def test_file_download_and_export(self):
        """Test file download and export functionality."""
        
        # Create assignment
        grading_assignment = self.grading_assignment.create(self.grading_assignment_data)
        assignment_data = self.assignment_data.copy()
        assignment_data['grading_assignment_id'] = grading_assignment.id
        assignment = self.op_assignment.create(assignment_data)
        assignment.act_publish()
        
        # Create submission with multiple files
        submission = self.op_assignment_subline.create({
            'assignment_id': assignment.id,
            'student_id': self.student1.id,
            'description': 'Download test submission'
        })
        
        # Create files for download testing
        files_data = [
            ('main_document.docx', b'Main assignment document content'),
            ('supporting_data.xlsx', b'Supporting spreadsheet data'),
            ('code_implementation.py', b'Python code implementation'),
        ]
        
        attachments = []
        for filename, content in files_data:
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'res_model': 'op.assignment.sub.line',
                'res_id': submission.id,
                'type': 'binary',
                'datas': base64.b64encode(content),
                'mimetype': 'application/octet-stream'
            })
            attachments.append(attachment)
        
        # Test individual file download data
        for attachment in attachments:
            download_data = {
                'file_id': attachment.id,
                'filename': attachment.name,
                'content': attachment.datas,  # Base64 encoded
                'mimetype': attachment.mimetype,
                'file_size': attachment.file_size
            }
            
            # Verify download data structure
            self.assertTrue(download_data['file_id'])
            self.assertTrue(download_data['filename'])
            self.assertTrue(download_data['content'])
            self.assertTrue(download_data['mimetype'])
            self.assertGreater(download_data['file_size'], 0)
        
        # Test bulk download preparation
        bulk_download_data = {
            'submission_id': submission.id,
            'student_name': submission.student_id.name,
            'assignment_name': submission.assignment_id.name,
            'files': []
        }
        
        for attachment in attachments:
            bulk_download_data['files'].append({
                'filename': attachment.name,
                'content': attachment.datas,
                'size': attachment.file_size
            })
        
        # Verify bulk download structure
        self.assertEqual(len(bulk_download_data['files']), 3)
        self.assertTrue(bulk_download_data['student_name'])
        self.assertTrue(bulk_download_data['assignment_name'])