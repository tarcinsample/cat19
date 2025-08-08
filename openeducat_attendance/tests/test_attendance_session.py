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

from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .test_attendance_common import TestAttendanceCommon


@tagged('post_install', '-at_install', 'openeducat_attendance')
class TestAttendanceSession(TestAttendanceCommon):
    """Test attendance session management and time tracking."""

    def setUp(self):
        """Set up additional session test data."""
        super().setUp()
        
        # Create session with course and batch
        self.session_with_course = self.env['op.session'].create({
            'name': 'Math Session 1',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'subject_id': self.subject.id,
            'faculty_id': self.faculty.id,
        })

    def test_session_attendance_sheet_relation(self):
        """Test One2many relation between session and attendance sheets."""
        # Create attendance sheet linked to session
        sheet = self.create_attendance_sheet(session_id=self.session_with_course.id)
        
        self.assertIn(sheet, self.session_with_course.attendance_sheet,
                     "Sheet should be linked to session")
        self.assertEqual(sheet.session_id, self.session_with_course,
                        "Sheet should reference the session")

    def test_get_attendance_no_course_batch(self):
        """Test get_attendance validation when session lacks course/batch."""
        session_incomplete = self.env['op.session'].create({
            'name': 'Incomplete Session',
            'start_datetime': datetime.now(),
            'end_datetime': datetime.now() + timedelta(hours=1),
        })
        
        with self.assertRaises(ValidationError) as context:
            session_incomplete.get_attendance()
        
        self.assertIn('course and batch configured', str(context.exception),
                     "Should validate course and batch requirement")

    def test_get_attendance_no_register(self):
        """Test get_attendance when no attendance register exists."""
        # Create session with different course (no register)
        other_course = self.env['op.course'].create({
            'name': 'Other Course',
            'code': 'OC001',
            'department_id': self.department.id,
        })
        
        other_batch = self.env['op.batch'].create({
            'name': 'Other Batch',
            'code': 'OB001',
            'course_id': other_course.id,
        })
        
        session = self.env['op.session'].create({
            'name': 'Session No Register',
            'course_id': other_course.id,
            'batch_id': other_batch.id,
            'start_datetime': datetime.now(),
            'end_datetime': datetime.now() + timedelta(hours=1),
        })
        
        with self.assertRaises(ValidationError) as context:
            session.get_attendance()
        
        self.assertIn('No attendance register found', str(context.exception),
                     "Should validate register existence")

    def test_get_attendance_create_new_sheet(self):
        """Test creating new attendance sheet when none exists."""
        action = self.session_with_course.get_attendance()
        
        self.assertEqual(action['res_model'], 'op.attendance.sheet',
                        "Should return attendance sheet action")
        self.assertEqual(action['view_mode'], 'form',
                        "Should open form view for new sheet")
        self.assertIn('default_session_id', action['context'],
                     "Should set session in context")
        self.assertIn('default_register_id', action['context'],
                     "Should set register in context")

    def test_get_attendance_single_existing_sheet(self):
        """Test opening single existing attendance sheet."""
        # Create existing sheet
        sheet = self.create_attendance_sheet(session_id=self.session_with_course.id)
        
        action = self.session_with_course.get_attendance()
        
        self.assertEqual(action['res_model'], 'op.attendance.sheet',
                        "Should return attendance sheet action")
        self.assertEqual(action['res_id'], sheet.id,
                        "Should open existing sheet")
        self.assertEqual(action['view_mode'], 'form',
                        "Should open form view")

    def test_get_attendance_multiple_existing_sheets(self):
        """Test list view when multiple attendance sheets exist."""
        # Create multiple sheets for same session
        sheet1 = self.create_attendance_sheet(
            session_id=self.session_with_course.id,
            attendance_date=self.today)
        sheet2 = self.create_attendance_sheet(
            session_id=self.session_with_course.id,
            attendance_date=self.yesterday)
        
        action = self.session_with_course.get_attendance()
        
        self.assertEqual(action['res_model'], 'op.attendance.sheet',
                        "Should return attendance sheet action")
        self.assertEqual(action['view_mode'], 'list,form',
                        "Should show list view for multiple sheets")
        self.assertIn('domain', action,
                     "Should include domain filter")
        self.assertEqual(action['domain'], [('session_id', '=', self.session_with_course.id)],
                        "Should filter by session")

    def test_session_attendance_context_defaults(self):
        """Test default context values in attendance actions."""
        action = self.session_with_course.get_attendance()
        
        context = action['context']
        self.assertEqual(context['default_session_id'], self.session_with_course.id,
                        "Should set session ID in context")
        self.assertEqual(context['default_register_id'], self.register.id,
                        "Should set register ID in context")

    def test_session_multiple_registers_selection(self):
        """Test register selection when multiple registers exist."""
        # Create additional register for same course/batch but different subject
        subject2 = self.env['op.subject'].create({
            'name': 'Test Subject 2',
            'code': 'TS002',
        })
        
        register2 = self.env['op.attendance.register'].create({
            'name': 'Test Register 2',
            'code': 'TR002',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'subject_id': subject2.id,
        })
        
        action = self.session_with_course.get_attendance()
        
        # Should find first register (ordered by search)
        context = action['context']
        self.assertTrue(context['default_register_id'] in [self.register.id, register2.id],
                       "Should select one of the available registers")

    def test_session_attendance_sheet_cascade(self):
        """Test that deleting session affects related sheets appropriately."""
        # Create attendance sheet linked to session
        sheet = self.create_attendance_sheet(session_id=self.session_with_course.id)
        sheet_id = sheet.id
        
        # Delete session
        self.session_with_course.unlink()
        
        # Check sheet still exists but session link is cleared
        remaining_sheet = self.env['op.attendance.sheet'].browse(sheet_id)
        if remaining_sheet.exists():
            self.assertFalse(remaining_sheet.session_id,
                           "Session reference should be cleared")

    def test_session_attendance_filtering(self):
        """Test filtering attendance sheets by session."""
        # Create sheets for different sessions
        sheet1 = self.create_attendance_sheet(session_id=self.session_with_course.id)
        
        other_session = self.env['op.session'].create({
            'name': 'Other Session',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'start_datetime': datetime.now(),
            'end_datetime': datetime.now() + timedelta(hours=1),
        })
        sheet2 = self.create_attendance_sheet(session_id=other_session.id)
        
        # Filter sheets by session
        session1_sheets = self.env['op.attendance.sheet'].search([
            ('session_id', '=', self.session_with_course.id)
        ])
        
        self.assertIn(sheet1, session1_sheets,
                     "Should find sheet for session 1")
        self.assertNotIn(sheet2, session1_sheets,
                        "Should not find sheet for other session")

    def test_session_attendance_performance(self):
        """Test performance with multiple attendance operations."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = self.env['op.session'].create({
                'name': f'Performance Session {i}',
                'course_id': self.course.id,
                'batch_id': self.batch.id,
                'subject_id': self.subject.id,
                'start_datetime': datetime.now() + timedelta(hours=i),
                'end_datetime': datetime.now() + timedelta(hours=i+1),
            })
            sessions.append(session)
        
        # Test batch attendance sheet creation
        for session in sessions:
            action = session.get_attendance()
            self.assertEqual(action['res_model'], 'op.attendance.sheet',
                           f"Should handle session {session.name}")

    def test_session_attendance_integration_workflow(self):
        """Test complete integration workflow for session attendance."""
        # Step 1: Get attendance (creates new sheet)
        action = self.session_with_course.get_attendance()
        
        # Step 2: Create the sheet using context
        sheet = self.env['op.attendance.sheet'].create({
            'register_id': action['context']['default_register_id'],
            'session_id': action['context']['default_session_id'],
            'attendance_date': self.today,
        })
        
        # Step 3: Verify sheet is linked to session
        self.assertEqual(sheet.session_id, self.session_with_course,
                        "Sheet should be linked to session")
        
        # Step 4: Get attendance again (should return existing sheet)
        action2 = self.session_with_course.get_attendance()
        self.assertEqual(action2['res_id'], sheet.id,
                        "Should return existing sheet")

    def test_session_attendance_error_handling(self):
        """Test error handling in session attendance operations."""
        # Test with session that has no subjects
        session_no_subject = self.env['op.session'].create({
            'name': 'No Subject Session',
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'start_datetime': datetime.now(),
            'end_datetime': datetime.now() + timedelta(hours=1),
        })
        
        # Should still work (register doesn't require subject match)
        action = session_no_subject.get_attendance()
        self.assertEqual(action['res_model'], 'op.attendance.sheet',
                        "Should handle session without specific subject")

    def test_session_attendance_action_target(self):
        """Test action target configuration."""
        action = self.session_with_course.get_attendance()
        
        self.assertEqual(action['target'], 'current',
                        "Should open in current window")
        self.assertEqual(action['type'], 'ir.actions.act_window',
                        "Should be window action")