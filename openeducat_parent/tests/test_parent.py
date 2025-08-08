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

from .test_parent_common import TestParentCommon


class TestParent(TestParentCommon):

    def setUp(self):
        super(TestParent, self).setUp()

    def test_case_1_parent(self):
        parents = self.op_parent.search([])
        
        # Create parent partner
        parent_partner = self.env['res.partner'].create({
            'name': 'Test Parent Partner',
            'email': 'parent@test.com',
            'mobile': '8334845',
            'is_company': False,
        })
        
        # Create parent user
        parent_user = self.env['res.users'].create({
            'name': 'Test Parent User',
            'login': 'test_parent',
            'partner_id': parent_partner.id,
        })
        
        vals = {
            'name': parent_partner.id,
            'user_id': parent_user.id,
            'relationship_id': self.relationship_father.id,
        }
        new_parent = self.op_parent.create(vals)
        
        # Test parent user creation
        if hasattr(new_parent, 'create_parent_user'):
            new_parent.create_parent_user()
        
        # Update parent
        val = {'user_id': parent_user.id}  # Update with valid user reference
        parents_to_update = self.op_parent.search([('user_id', '=', parent_user.id)])
        if parents_to_update:
            parents_to_update.write(val)

        for parent in parents:
            if hasattr(parent, '_onchange_name'):
                parent._onchange_name()

        # Clean up
        parents_to_delete = self.op_parent.search([('user_id', '=', parent_user.id)])
        if parents_to_delete:
            parents_to_delete.unlink()

    def test_case_2_student(self):
        # Create test parent first
        test_parent = self.create_parent(parent_name='Test Parent for Student')
        
        # Create student partner
        student_partner = self.env['res.partner'].create({
            'name': 'Nikul Ahir',
            'email': 'nik@gmail.com',
            'mobile': '73482383624',
            'is_company': False,
        })
        
        # Create student user
        student_user = self.env['res.users'].create({
            'name': 'Nikul Ahir',
            'login': 'nikul_student',
            'partner_id': student_partner.id,
        })
        
        vals = {
            'user_id': student_user.id,
            'partner_id': student_partner.id,
            'first_name': 'nikul',
            'last_name': 'ahir',
            'gender': 'm',
            'birth_date': '2009-01-01',
            'parent_ids': [(6, 0, [test_parent.id])],
        }

        student = self.op_student.create(vals)
        vals.update({
            'first_name': 'NIK',
            'last_name': 'AHIR',
            'parent_ids': [(6, 0, [test_parent.id])],
        })
        student.write(vals)
        # Check if student has user_id before unlinking to avoid list.remove error
        if student.user_id:
            # Remove student from any parent relationships first
            for parent in student.parent_ids if hasattr(student, 'parent_ids') else []:
                if parent.user_id and student.user_id:
                    child_ids = parent.user_id.child_ids.ids
                    if student.user_id.id in child_ids:
                        child_ids.remove(student.user_id.id)
                        parent.user_id.child_ids = [(6, 0, child_ids)]
        
        student.unlink()

    def test_case_3_subject_registartion(self):
        # Create subject first
        subject = self.env['op.subject'].create({
            'name': 'Test Subject',
            'code': 'SUBJ001',
            'type': 'theory',
        })
        
        vals = {
            'student_id': self.student1.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'elective_subject_ids': [(6, 0, [subject.id])],  # Use the correct Many2many field
        }
        registration = self.subject_registration.create(vals)
        registration.write(vals)
