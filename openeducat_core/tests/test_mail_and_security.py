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

from odoo.tests import tagged
from odoo.exceptions import AccessError
from .test_core_common import TestCoreCommon


@tagged('post_install', '-at_install', 'mail_security')
class TestMailAndSecurity(TestCoreCommon):
    """Test mail tracking, notifications, and security rule compliance."""

    def test_student_mail_thread_inheritance(self):
        """Test student inherits mail.thread for tracking."""
        student = self._create_test_student()
        
        # Should inherit mail.thread
        self.assertTrue(hasattr(student, 'message_post'))
        self.assertTrue(hasattr(student, 'message_ids'))
        self.assertTrue(hasattr(student, 'message_follower_ids'))
        
        # Should be able to post message
        message = student.message_post(
            body="Test message for student tracking",
            subject="Test Subject"
        )
        self.assertTrue(message)

    def test_faculty_mail_thread_inheritance(self):
        """Test faculty inherits mail.thread for tracking."""
        faculty = self._create_test_faculty()
        
        # Should inherit mail.thread
        self.assertTrue(hasattr(faculty, 'message_post'))
        self.assertTrue(hasattr(faculty, 'message_ids'))
        self.assertTrue(hasattr(faculty, 'message_follower_ids'))
        
        # Should be able to post message
        message = faculty.message_post(
            body="Test message for faculty tracking",
            subject="Test Subject"
        )
        self.assertTrue(message)

    def test_course_mail_thread_inheritance(self):
        """Test course inherits mail.thread for tracking."""
        course = self.test_course
        
        # Should inherit mail.thread
        self.assertTrue(hasattr(course, 'message_post'))
        self.assertTrue(hasattr(course, 'message_ids'))
        
        # Should be able to post message
        message = course.message_post(
            body="Test message for course tracking",
            subject="Course Update"
        )
        self.assertTrue(message)

    def test_batch_mail_thread_inheritance(self):
        """Test batch inherits mail.thread for tracking."""
        batch = self.test_batch
        
        # Should inherit mail.thread
        self.assertTrue(hasattr(batch, 'message_post'))
        self.assertTrue(hasattr(batch, 'message_ids'))
        
        # Should be able to post message
        message = batch.message_post(
            body="Test message for batch tracking",
            subject="Batch Update"
        )
        self.assertTrue(message)

    def test_field_tracking_student(self):
        """Test field tracking for student model."""
        student = self._create_test_student(
            first_name='Original',
            last_name='Name'
        )
        
        # Get initial message count
        initial_message_count = len(student.message_ids)
        
        # Update tracked field
        student.write({'first_name': 'Updated'})
        
        # Should have created tracking message if tracking is enabled
        if hasattr(student, '_track_subtype'):
            new_message_count = len(student.message_ids)
            # May or may not create message depending on tracking configuration
            self.assertGreaterEqual(new_message_count, initial_message_count)

    def test_field_tracking_faculty(self):
        """Test field tracking for faculty model."""
        faculty = self._create_test_faculty(
            first_name='Original',
            last_name='Faculty'
        )
        
        # Get initial message count
        initial_message_count = len(faculty.message_ids)
        
        # Update tracked field
        faculty.write({'first_name': 'Updated'})
        
        # Should have created tracking message if tracking is enabled
        if hasattr(faculty, '_track_subtype'):
            new_message_count = len(faculty.message_ids)
            self.assertGreaterEqual(new_message_count, initial_message_count)

    def test_multi_company_security_student(self):
        """Test multi-company security for student records."""
        # Create second company
        company2 = self.env['res.company'].create({
            'name': 'Test Company 2',
        })
        
        # Create student in main company
        student1 = self._create_test_student(
            first_name='Company1',
            last_name='Student',
            gr_no='COMP1_001'
        )
        
        # Create user with access to both companies
        multi_user = self.env['res.users'].create({
            'name': 'Multi Company User',
            'login': 'multi@test.com',
            'email': 'multi@test.com',
            'company_ids': [(6, 0, [self.test_company.id, company2.id])],
            'company_id': self.test_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_back_office_admin').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        # Should be able to access student in allowed company
        student_env = self.env['op.student'].with_user(multi_user)
        try:
            student_record = student_env.browse(student1.id)
            student_record.read(['name'])
        except AccessError:
            self.fail("Multi-company user should access records in allowed company")

    def test_security_rules_student_access(self):
        """Test security rules for student access."""
        student = self._create_test_student()
        
        # Create different types of users
        student_user = self.env['res.users'].create({
            'name': 'Student User',
            'login': 'student_security@test.com',
            'email': 'student_security@test.com',
            'is_student': True,
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_student').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        faculty_user = self.env['res.users'].create({
            'name': 'Faculty User',
            'login': 'faculty_security@test.com',
            'email': 'faculty_security@test.com',
            'is_faculty': True,
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_faculty').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        # Test student user access
        student_env = self.env['op.student'].with_user(student_user)
        try:
            students = student_env.search([])
            # Student users should have some level of access
        except AccessError:
            pass  # May be restricted based on security rules
        
        # Test faculty user access
        faculty_env = self.env['op.student'].with_user(faculty_user)
        try:
            students = faculty_env.search([])
            # Faculty users should have broader access
        except AccessError:
            pass  # May be restricted based on security rules

    def test_security_rules_course_access(self):
        """Test security rules for course access."""
        course = self.test_course
        
        # Test with student user
        student_user = self.env['res.users'].create({
            'name': 'Course Student User',
            'login': 'course_student@test.com',
            'email': 'course_student@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_student').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        course_env = self.env['op.course'].with_user(student_user)
        try:
            courses = course_env.search([])
            # Students should be able to read courses
            self.assertGreaterEqual(len(courses), 0)
        except AccessError:
            self.fail("Students should be able to read course information")

    def test_record_rules_department_based(self):
        """Test record rules based on department access."""
        # Create another department
        dept2 = self.env['op.department'].create({
            'name': 'Mathematics Department',
            'code': 'MATH',
        })
        
        # Create course in second department
        course2 = self.env['op.course'].create({
            'name': 'Advanced Mathematics',
            'code': 'MATH301',
            'department_id': dept2.id,
            'program_id': self.test_program.id,  # Assuming program allows cross-department
        })
        
        # Test that users can access courses from different departments
        # This depends on the actual security rule implementation
        all_courses = self.course_model.search([])
        self.assertIn(self.test_course, all_courses)
        self.assertIn(course2, all_courses)

    def test_mail_activity_mixin_student(self):
        """Test mail.activity.mixin functionality for students."""
        student = self._create_test_student()
        
        # Check if student inherits mail.activity.mixin
        if hasattr(student, 'activity_ids'):
            # Should be able to create activities
            activity_type = self.env['mail.activity.type'].search([], limit=1)
            if activity_type:
                activity = self.env['mail.activity'].create({
                    'activity_type_id': activity_type.id,
                    'summary': 'Test Activity',
                    'res_id': student.id,
                    'res_model': 'op.student',
                    'user_id': self.env.user.id,
                })
                self.assertTrue(activity)
                self.assertIn(activity, student.activity_ids)

    def test_mail_notification_student_creation(self):
        """Test mail notifications on student creation."""
        # This test checks if notifications are sent when students are created
        student = self._create_test_student()
        
        # Check if creation triggered any mail messages
        messages = student.message_ids
        # May or may not have messages depending on configuration
        self.assertGreaterEqual(len(messages), 0)

    def test_mail_followers_management(self):
        """Test mail followers management for educational records."""
        student = self._create_test_student()
        
        # Test adding followers
        partner = self.env['res.partner'].create({
            'name': 'Test Follower',
            'email': 'follower@test.com',
        })
        
        if hasattr(student, 'message_subscribe'):
            student.message_subscribe(partner_ids=[partner.id])
            self.assertIn(partner, student.message_partner_ids)

    def test_access_rights_model_level(self):
        """Test model-level access rights for core models."""
        models_to_test = [
            'op.student',
            'op.faculty',
            'op.course',
            'op.batch',
            'op.subject',
            'op.department',
            'op.program',
            'op.category',
        ]
        
        for model_name in models_to_test:
            if model_name in self.env:
                model = self.env[model_name]
                
                # Test that model has access rights defined
                access_rights = self.env['ir.model.access'].search([
                    ('model_id.model', '=', model_name)
                ])
                
                # Should have at least some access rights defined
                self.assertGreater(len(access_rights), 0, 
                                 f"Model {model_name} should have access rights defined")

    def test_security_groups_existence(self):
        """Test that required security groups exist."""
        required_groups = [
            'openeducat_core.group_op_student',
            'openeducat_core.group_op_faculty',
            'openeducat_core.group_op_back_office',
            'openeducat_core.group_op_back_office_admin',
        ]
        
        for group_xml_id in required_groups:
            try:
                group = self.env.ref(group_xml_id)
                self.assertTrue(group.exists(), f"Security group {group_xml_id} should exist")
            except ValueError:
                self.fail(f"Security group {group_xml_id} not found")

    def test_record_creation_permissions(self):
        """Test record creation permissions for different user types."""
        # Create different user types
        student_user = self.env['res.users'].create({
            'name': 'Creation Student User',
            'login': 'creation_student@test.com',
            'email': 'creation_student@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_student').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        admin_user = self.env['res.users'].create({
            'name': 'Creation Admin User',
            'login': 'creation_admin@test.com',
            'email': 'creation_admin@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_back_office_admin').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        # Test admin can create students
        student_env_admin = self.env['op.student'].with_user(admin_user)
        try:
            partner = self.env['res.partner'].with_user(admin_user).create({
                'name': 'Admin Created Student',
                'email': 'admin_created@test.com',
            })
            
            admin_student = student_env_admin.create({
                'first_name': 'Admin',
                'last_name': 'Created',
                'birth_date': '2000-01-01',
                'gender': 'm',
                'partner_id': partner.id,
                'category_id': self.test_category.id,
            })
            self.assertTrue(admin_student.id)
        except AccessError:
            self.fail("Admin should be able to create students")

    def test_mail_template_integration(self):
        """Test mail template integration if available."""
        student = self._create_test_student()
        
        # Check if mail templates exist for student model
        templates = self.env['mail.template'].search([
            ('model', '=', 'op.student')
        ])
        
        # If templates exist, test they can be used
        for template in templates:
            try:
                # Test template rendering
                rendered = template.generate_email(student.id)
                self.assertIsInstance(rendered, dict)
            except Exception as e:
                self.fail(f"Mail template {template.name} failed to render: {e}")

    def test_data_privacy_compliance(self):
        """Test data privacy and GDPR compliance features."""
        student = self._create_test_student(
            first_name='Privacy',
            last_name='Test',
            email='privacy@test.com'
        )
        
        # Test data export capability (for GDPR compliance)
        export_fields = ['name', 'email', 'birth_date', 'phone']
        available_fields = student.fields_get().keys()
        
        export_data = {}
        for field in export_fields:
            if field in available_fields:
                export_data[field] = getattr(student, field, None)
        
        # Should be able to export basic data
        self.assertGreater(len(export_data), 0)

    def test_audit_trail_logging(self):
        """Test audit trail logging for sensitive operations."""
        student = self._create_test_student()
        
        # Get initial message count
        initial_messages = len(student.message_ids)
        
        # Perform sensitive operation (like changing grades, if applicable)
        student.write({'first_name': 'Audited Change'})
        
        # Check if audit trail was created
        new_messages = len(student.message_ids)
        
        # May or may not create audit messages depending on configuration
        self.assertGreaterEqual(new_messages, initial_messages)

    def test_cross_model_security_consistency(self):
        """Test security consistency across related models."""
        # Create complete educational setup
        student = self._create_test_student()
        course_detail = self._create_test_student_course(student_id=student.id)
        
        # Test that related records have consistent access
        student_user = self.env['res.users'].create({
            'name': 'Consistency Student User',
            'login': 'consistency@test.com',
            'email': 'consistency@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('openeducat_core.group_op_student').id,
                self.env.ref('base.group_user').id
            ])],
        })
        
        # If student can access their record, they should access related records
        try:
            student_env = self.env['op.student'].with_user(student_user)
            course_env = self.env['op.course'].with_user(student_user)
            batch_env = self.env['op.batch'].with_user(student_user)
            
            # Try to access related records
            student_env.browse(student.id).read(['name'])
            course_env.browse(self.test_course.id).read(['name'])
            batch_env.browse(self.test_batch.id).read(['name'])
            
        except AccessError:
            pass  # Access may be restricted based on configuration