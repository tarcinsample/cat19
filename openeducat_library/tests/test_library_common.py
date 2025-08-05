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

from datetime import date, timedelta
import uuid
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'openeducat_library')
class TestLibraryCommon(TransactionCase):
    """Common test setup for library module tests."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for library tests."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create academic year
        cls.academic_year = cls.env['op.academic.year'].create({
            'name': 'Test Year 2024-25',
            
            'start_date': '2024-06-01',
            'end_date': '2025-05-31',
        })
        
        # Create academic term
        cls.academic_term = cls.env['op.academic.term'].create({
            'name': 'Test Term 1',
            
            'term_start_date': '2024-06-01',
            'term_end_date': '2024-12-31',
            'academic_year_id': cls.academic_year.id,
        })
        
        # Create department
        cls.department = cls.env['op.department'].create({
            'name': 'Test Department',
            'code': 'TD001',
        })
        
        # Create course
        cls.course = cls.env['op.course'].create({
            'name': 'Test Course',
            'code': 'TC001',
            'department_id': cls.department.id,
        })
        
        # Create batch
        cls.batch = cls.env['op.batch'].create({
            'name': 'Test Batch',
            'code': 'TB001_' + str(uuid.uuid4())[:8].replace('-', ''),
            'course_id': cls.course.id,
            'start_date': '2024-06-01',
            'end_date': '2024-12-31',
        })
        
        # Create students with required partners
        partner1 = cls.env['res.partner'].create({
            'name': 'Test Student 1',
            'is_company': False,
        })
        cls.student1 = cls.env['op.student'].create({
            'partner_id': partner1.id,
            'first_name': 'Test',
            'last_name': 'Student1',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        partner2 = cls.env['res.partner'].create({
            'name': 'Test Student 2',
            'is_company': False,
        })
        cls.student2 = cls.env['op.student'].create({
            'partner_id': partner2.id,
            'first_name': 'Test',
            'last_name': 'Student2',
            'birth_date': '2000-02-02',
            'gender': 'f',
            'course_detail_ids': [(0, 0, {
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
                'academic_years_id': cls.academic_year.id,
                'academic_term_id': cls.academic_term.id,
            })],
        })
        
        # Create faculty with required fields
        faculty_partner = cls.env['res.partner'].create({
            'name': 'Test Faculty',
            'is_company': False,
        })
        cls.faculty = cls.env['op.faculty'].create({
            'partner_id': faculty_partner.id,
            'first_name': 'Test',
            'last_name': 'Faculty',
            'birth_date': '1980-01-01',
            'gender': 'male',
        })
        
        # Create library card type
        cls.card_type = cls.env['op.library.card.type'].create({
            'name': 'Student Card',
            'allow_day': 7,
            'penalties_day': 1.0,
        })
        
        # Create authors
        cls.author1 = cls.env['op.author'].create({
            'name': 'Test Author 1',
            'birth_date': '1970-01-01',
            'country_id': cls.env.ref('base.us').id,
        })
        
        cls.author2 = cls.env['op.author'].create({
            'name': 'Test Author 2',
            'birth_date': '1975-02-02',
            'country_id': cls.env.ref('base.uk').id,
        })
        
        # Create publisher
        cls.publisher = cls.env['op.publisher'].create({
            'name': 'Test Publisher',
            'website': 'https://testpublisher.com',
        })
        
        # Create media types
        cls.media_type_book = cls.env['op.media.type'].create({
            'name': 'Book',
            'code': 'BOOK',
        })
        
        cls.media_type_journal = cls.env['op.media.type'].create({
            'name': 'Journal',
            'code': 'JOURNAL',
        })
        
        # Create media units
        cls.media_unit = cls.env['op.media.unit'].create({
            'name': 'Central Library',
            'code': 'CL001',
        })
        
        # Create tags
        cls.tag_science = cls.env['op.tag'].create({
            'name': 'Science',
        })
        
        cls.tag_fiction = cls.env['op.tag'].create({
            'name': 'Fiction',
        })
        
        # Helper methods
        cls.today = date.today()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

    def create_media(self, **kwargs):
        """Helper method to create media."""
        vals = {
            'name': 'Test Book',
            'isbn': '978-0123456789',
            'author_ids': [(6, 0, [self.author1.id])],
            'publisher_id': self.publisher.id,
            'media_type': self.media_type_book.id,
            'unit_id': self.media_unit.id,
            'tag_ids': [(6, 0, [self.tag_science.id])],
            'state': 'available',
        }
        vals.update(kwargs)
        return self.env['op.media'].create(vals)

    def create_library_card(self, student, **kwargs):
        """Helper method to create library card."""
        vals = {
            'student_id': student.id,
            'card_type_id': self.card_type.id,
        }
        vals.update(kwargs)
        return self.env['op.library.card'].create(vals)

    def create_media_movement(self, media, student, movement_type='issue', **kwargs):
        """Helper method to create media movement."""
        vals = {
            'media_id': media.id,
            'student_id': student.id,
            'type': movement_type,
            'issue_date': self.today,
        }
        if movement_type == 'issue':
            vals['return_date'] = self.today + timedelta(days=7)
        vals.update(kwargs)
        return self.env['op.media.movement'].create(vals)

    def create_media_queue(self, media, student, **kwargs):
        """Helper method to create media queue entry."""
        vals = {
            'media_id': media.id,
            'student_id': student.id,
            'request_date': self.today,
        }
        vals.update(kwargs)
        return self.env['op.media.queue'].create(vals)
