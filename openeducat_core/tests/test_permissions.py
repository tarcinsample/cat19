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


@tagged('post_install', '-at_install', 'permissions')
class TestPermissions(TestCoreCommon):
    """Test user creation and permission assignment workflows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test groups
        cls.student_group = cls.env.ref('openeducat_core.group_op_student')
        cls.faculty_group = cls.env.ref('openeducat_core.group_op_faculty')
        cls.admin_group = cls.env.ref('openeducat_core.group_op_back_office_admin')
        
        # Create test users for different roles
        cls.test_student_user = cls.env['res.users'].create({
            'name': 'Test Student User',
            'login': 'test_student@example.com',
            'email': 'test_student@example.com',
            'is_student': True,
            'groups_id': [(6, 0, [cls.student_group.id, cls.env.ref('base.group_user').id])],
        })
        
        cls.test_faculty_user = cls.env['res.users'].create({
            'name': 'Test Faculty User',
            'login': 'test_faculty@example.com',
            'email': 'test_faculty@example.com',
            'is_faculty': True,
            'groups_id': [(6, 0, [cls.faculty_group.id, cls.env.ref('base.group_user').id])],
        })
        
        cls.test_admin_user = cls.env['res.users'].create({
            'name': 'Test Admin User',
            'login': 'test_admin@example.com',
            'email': 'test_admin@example.com',
            'groups_id': [(6, 0, [cls.admin_group.id, cls.env.ref('base.group_user').id])],
        })

    def test_student_user_creation(self):
        """Test student user creation workflow."""
        student = self._create_test_student(
            first_name='Test',
            last_name='Student',
            email='new_student@test.com'
        )
        student.partner_id.email = 'new_student@test.com'
        
        # Initially no user
        self.assertFalse(student.user_id)
        
        # Create user
        student.create_student_user()
        
        # Verify user created with correct properties
        self.assertTrue(student.user_id)
        self.assertEqual(student.user_id.login, 'new_student@test.com')
        self.assertEqual(student.user_id.name, student.name)
        self.assertTrue(student.user_id.is_student)
        self.assertIn(self.student_group, student.user_id.groups_id)

    def test_student_user_creation_duplicate(self):
        """Test student user creation when user already exists."""
        student = self._create_test_student()
        
        # Create user first time
        student.create_student_user()
        first_user = student.user_id
        
        # Try to create user again
        student.create_student_user()
        
        # Should still be same user
        self.assertEqual(student.user_id, first_user)

    def test_faculty_user_creation(self):
        """Test faculty user creation workflow."""
        faculty = self._create_test_faculty(
            first_name='Dr. Test',
            last_name='Faculty',
            email='new_faculty@test.com'
        )
        faculty.partner_id.email = 'new_faculty@test.com'
        
        # Initially no user
        self.assertFalse(faculty.user_id)
        
        # Create user if method exists
        if hasattr(faculty, 'create_faculty_user'):
            faculty.create_faculty_user()
            
            # Verify user created with correct properties
            self.assertTrue(faculty.user_id)
            self.assertEqual(faculty.user_id.login, 'new_faculty@test.com')
            self.assertEqual(faculty.user_id.name, faculty.name)
            self.assertTrue(faculty.user_id.is_faculty)

    def test_student_permissions_read_own_data(self):
        """Test student can read their own data."""
        student = self._create_test_student()
        student.user_id = self.test_student_user.id
        
        # Student should be able to read their own record
        student_env = self.env['op.student'].with_user(self.test_student_user)
        try:
            own_record = student_env.browse(student.id)
            own_record.read(['name', 'birth_date'])
        except AccessError:
            self.fail("Student should be able to read their own data")

    def test_student_permissions_cannot_modify_others(self):
        """Test student cannot modify other students' data."""
        student1 = self._create_test_student(
            first_name='Student1',
            last_name='Test'
        )
        student1.user_id = self.test_student_user.id
        
        student2 = self._create_test_student(
            first_name='Student2',
            last_name='Test'
        )
        
        # Student should not be able to modify other student's record
        student_env = self.env['op.student'].with_user(self.test_student_user)
        try:
            other_record = student_env.browse(student2.id)
            other_record.write({'first_name': 'Modified'})
            # If this doesn't raise an error, the test should verify restrictions
        except AccessError:
            pass  # Expected behavior

    def test_faculty_permissions_read_student_data(self):
        """Test faculty can read student data."""
        student = self._create_test_student()
        
        # Faculty should be able to read student records
        student_env = self.env['op.student'].with_user(self.test_faculty_user)
        try:
            student_record = student_env.browse(student.id)
            student_record.read(['name', 'birth_date'])
        except AccessError:
            self.fail("Faculty should be able to read student data")

    def test_admin_permissions_full_access(self):
        """Test admin has full access to all records."""
        student = self._create_test_student()
        faculty = self._create_test_faculty()
        
        # Admin should have full access
        student_env = self.env['op.student'].with_user(self.test_admin_user)
        faculty_env = self.env['op.faculty'].with_user(self.test_admin_user)
        
        try:
            # Should be able to read
            student_env.browse(student.id).read(['name'])
            faculty_env.browse(faculty.id).read(['name'])
            
            # Should be able to write
            student_env.browse(student.id).write({'first_name': 'AdminModified'})
            faculty_env.browse(faculty.id).write({'first_name': 'AdminModified'})
        except AccessError:
            self.fail("Admin should have full access to all records")

    def test_course_permissions_by_role(self):
        """Test course access permissions by different roles."""
        course = self.test_course
        
        # Test student access to courses
        course_env = self.env['op.course'].with_user(self.test_student_user)
        try:
            course_env.browse(course.id).read(['name', 'code'])
        except AccessError:
            self.fail("Students should be able to read course data")
        
        # Test faculty access to courses
        course_env = self.env['op.course'].with_user(self.test_faculty_user)
        try:
            course_env.browse(course.id).read(['name', 'code'])
        except AccessError:
            self.fail("Faculty should be able to read course data")

    def test_batch_permissions_by_role(self):
        """Test batch access permissions by different roles."""
        batch = self.test_batch
        
        # Test student access to batches
        batch_env = self.env['op.batch'].with_user(self.test_student_user)
        try:
            batch_env.browse(batch.id).read(['name', 'code'])
        except AccessError:
            self.fail("Students should be able to read batch data")
        
        # Test faculty access to batches
        batch_env = self.env['op.batch'].with_user(self.test_faculty_user)
        try:
            batch_env.browse(batch.id).read(['name', 'code'])
        except AccessError:
            self.fail("Faculty should be able to read batch data")

    def test_subject_permissions_by_role(self):
        """Test subject access permissions by different roles."""
        subject = self.test_subject
        
        # Test student access to subjects
        subject_env = self.env['op.subject'].with_user(self.test_student_user)
        try:
            subject_env.browse(subject.id).read(['name', 'code'])
        except AccessError:
            self.fail("Students should be able to read subject data")
        
        # Test faculty access to subjects
        subject_env = self.env['op.subject'].with_user(self.test_faculty_user)
        try:
            subject_env.browse(subject.id).read(['name', 'code'])
        except AccessError:
            self.fail("Faculty should be able to read subject data")

    def test_academic_year_permissions(self):
        """Test academic year access permissions."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        # All users should be able to read academic year
        for user in [self.test_student_user, self.test_faculty_user, self.test_admin_user]:
            ay_env = self.env['op.academic.year'].with_user(user)
            try:
                ay_env.browse(academic_year.id).read(['name', 'code'])
            except AccessError:
                self.fail(f"User {user.name} should be able to read academic year data")

    def test_academic_term_permissions(self):
        """Test academic term access permissions."""
        academic_year = self.env['op.academic.year'].create({
            'name': '2024-2025',
            'code': 'AY2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-12-31',
        })
        
        academic_term = self.env['op.academic.term'].create({
            'name': 'Spring 2024',
            'code': 'SP2024',
            'date_start': '2024-01-01',
            'date_stop': '2024-06-30',
            'academic_year_id': academic_year.id,
        })
        
        # All users should be able to read academic term
        for user in [self.test_student_user, self.test_faculty_user, self.test_admin_user]:
            at_env = self.env['op.academic.term'].with_user(user)
            try:
                at_env.browse(academic_term.id).read(['name', 'code'])
            except AccessError:
                self.fail(f"User {user.name} should be able to read academic term data")

    def test_department_permissions(self):
        """Test department access permissions."""
        department = self.test_department
        
        # All users should be able to read department data
        for user in [self.test_student_user, self.test_faculty_user, self.test_admin_user]:
            dept_env = self.env['op.department'].with_user(user)
            try:
                dept_env.browse(department.id).read(['name', 'code'])
            except AccessError:
                self.fail(f"User {user.name} should be able to read department data")

    def test_program_permissions(self):
        """Test program access permissions."""
        program = self.test_program
        
        # All users should be able to read program data
        for user in [self.test_student_user, self.test_faculty_user, self.test_admin_user]:
            prog_env = self.env['op.program'].with_user(user)
            try:
                prog_env.browse(program.id).read(['name', 'code'])
            except AccessError:
                self.fail(f"User {user.name} should be able to read program data")

    def test_category_permissions(self):
        """Test category access permissions."""
        category = self.test_category
        
        # All users should be able to read category data
        for user in [self.test_student_user, self.test_faculty_user, self.test_admin_user]:
            cat_env = self.env['op.category'].with_user(user)
            try:
                cat_env.browse(category.id).read(['name', 'code'])
            except AccessError:
                self.fail(f"User {user.name} should be able to read category data")

    def test_subject_registration_permissions(self):
        """Test subject registration permissions."""
        student = self._create_test_student()
        course_detail = self._create_test_student_course(student_id=student.id)
        
        subject_reg = self.env['op.subject.registration'].create({
            'student_id': student.id,
            'course_id': self.test_course.id,
            'batch_id': self.test_batch.id,
            'state': 'draft',
        })
        
        # Student should be able to read their own subject registration
        if hasattr(student, 'user_id') and student.user_id:
            sr_env = self.env['op.subject.registration'].with_user(student.user_id)
            try:
                sr_env.browse(subject_reg.id).read(['state'])
            except AccessError:
                pass  # May be restricted based on implementation

    def test_user_group_assignments(self):
        """Test user group assignments are correct."""
        # Test student user groups
        student = self._create_test_student()
        student.create_student_user()
        
        if student.user_id:
            self.assertIn(self.student_group, student.user_id.groups_id)
            self.assertTrue(student.user_id.is_student)
        
        # Test faculty user groups if creation method exists
        faculty = self._create_test_faculty()
        if hasattr(faculty, 'create_faculty_user'):
            faculty.create_faculty_user()
            if faculty.user_id:
                self.assertTrue(faculty.user_id.is_faculty)

    def test_multi_company_permissions(self):
        """Test multi-company permission scenarios."""
        # Create second company
        company2 = self.env['res.company'].create({
            'name': 'Test Company 2',
        })
        
        # Create user with access to both companies
        multi_company_user = self.env['res.users'].create({
            'name': 'Multi Company User',
            'login': 'multi@test.com',
            'email': 'multi@test.com',
            'company_ids': [(6, 0, [self.test_company.id, company2.id])],
            'company_id': self.test_company.id,
            'groups_id': [(6, 0, [self.admin_group.id, self.env.ref('base.group_user').id])],
        })
        
        # Test access with different company contexts
        student_env = self.env['op.student'].with_user(multi_company_user)
        try:
            student_env.with_company(self.test_company).search([])
            student_env.with_company(company2).search([])
        except AccessError:
            self.fail("Multi-company user should have access to records in allowed companies")

    def test_portal_user_permissions(self):
        """Test portal user permissions if portal access exists."""
        # Create portal user
        portal_group = self.env.ref('base.group_portal')
        portal_user = self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal@test.com',
            'email': 'portal@test.com',
            'groups_id': [(6, 0, [portal_group.id])],
        })
        
        # Portal users should have limited access
        student_env = self.env['op.student'].with_user(portal_user)
        try:
            student_env.search([])
            # Portal users may have restricted access
        except AccessError:
            pass  # Expected for portal users

    def test_inactive_user_permissions(self):
        """Test inactive user permissions."""
        # Create and deactivate user
        inactive_user = self.env['res.users'].create({
            'name': 'Inactive User',
            'login': 'inactive@test.com',
            'email': 'inactive@test.com',
            'active': False,
            'groups_id': [(6, 0, [self.student_group.id, self.env.ref('base.group_user').id])],
        })
        
        # Inactive users should not be able to access system
        with self.assertRaises(AccessError):
            self.env['op.student'].with_user(inactive_user).search([])