# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

###########################################################################
#
#    OpenEduCat Inc.
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
###########################################################################

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """Configuration settings for OpenEduCat modules and features.

    This model extends the base configuration settings to include OpenEduCat
    specific settings. It provides options to enable/disable various modules
    and configure system-wide settings.

    Attributes:
        module_openeducat_activity (bool): Enable activity module
        module_openeducat_facility (bool): Enable facility management
        module_openeducat_exam (bool): Enable examination management
        module_openeducat_timetable (bool): Enable timetable management
        module_openeducat_library (bool): Enable library management
        module_openeducat_transportation (bool): Enable transportation management
        module_openeducat_achievement (bool): Enable achievement tracking
        module_openeducat_parent (bool): Enable parent portal
        module_openeducat_discipline (bool): Enable discipline management
        module_openeducat_attendance (bool): Enable attendance tracking
        module_openeducat_health (bool): Enable health management
        module_openeducat_scholarship (bool): Enable scholarship management
        module_openeducat_fees (bool): Enable fee management
        module_openeducat_admission (bool): Enable admission management
        module_openeducat_alumni (bool): Enable alumni management
        module_openeducat_assignment (bool): Enable assignment management
        module_openeducat_online_admission (bool): Enable online admission
        module_openeducat_online_course (bool): Enable online courses
        module_openeducat_online_facility (bool): Enable online facility booking
        module_openeducat_online_library (bool): Enable online library
        module_openeducat_online_exam (bool): Enable online examinations
        module_openeducat_online_meeting (bool): Enable online meetings
        module_openeducat_online_timetable (bool): Enable online timetable
        module_openeducat_online_attendance (bool): Enable online attendance
        module_openeducat_online_assignment (bool): Enable online assignments
        module_openeducat_online_admission_enterprise (bool): Enable enterprise admission
        module_openeducat_online_course_enterprise (bool): Enable enterprise courses
        module_openeducat_online_facility_enterprise (bool): Enable enterprise facilities
        module_openeducat_online_library_enterprise (bool): Enable enterprise library
        module_openeducat_online_exam_enterprise (bool): Enable enterprise exams
        module_openeducat_online_meeting_enterprise (bool): Enable enterprise meetings
        module_openeducat_online_timetable_enterprise (bool): Enable enterprise timetable
        module_openeducat_online_attendance_enterprise (bool): Enable enterprise attendance
        module_openeducat_online_assignment_enterprise (bool): Enable enterprise assignments
        module_openeducat_online_admission_standard (bool): Enable standard admission
        module_openeducat_online_course_standard (bool): Enable standard courses
        module_openeducat_online_facility_standard (bool): Enable standard facilities
        module_openeducat_online_library_standard (bool): Enable standard library
        module_openeducat_online_exam_standard (bool): Enable standard exams
        module_openeducat_online_meeting_standard (bool): Enable standard meetings
        module_openeducat_online_timetable_standard (bool): Enable standard timetable
        module_openeducat_online_attendance_standard (bool): Enable standard attendance
        module_openeducat_online_assignment_standard (bool): Enable standard assignments
        module_openeducat_online_admission_professional (bool): Enable professional admission
        module_openeducat_online_course_professional (bool): Enable professional courses
        module_openeducat_online_facility_professional (bool): Enable professional facilities
        module_openeducat_online_library_professional (bool): Enable professional library
        module_openeducat_online_exam_professional (bool): Enable professional exams
        module_openeducat_online_meeting_professional (bool): Enable professional meetings
        module_openeducat_online_timetable_professional (bool): Enable professional timetable
        module_openeducat_online_attendance_professional (bool): Enable professional attendance
        module_openeducat_online_assignment_professional (bool): Enable professional assignments
        module_openeducat_online_admission_enterprise_standard (bool): Enable enterprise standard admission
        module_openeducat_online_course_enterprise_standard (bool): Enable enterprise standard courses
        module_openeducat_online_facility_enterprise_standard (bool): Enable enterprise standard facilities
        module_openeducat_online_library_enterprise_standard (bool): Enable enterprise standard library
        module_openeducat_online_exam_enterprise_standard (bool): Enable enterprise standard exams
        module_openeducat_online_meeting_enterprise_standard (bool): Enable enterprise standard meetings
        module_openeducat_online_timetable_enterprise_standard (bool): Enable enterprise standard timetable
        module_openeducat_online_attendance_enterprise_standard (bool): Enable enterprise standard attendance
        module_openeducat_online_assignment_enterprise_standard (bool): Enable enterprise standard assignments
        module_openeducat_online_admission_enterprise_professional (bool): Enable enterprise professional admission
        module_openeducat_online_course_enterprise_professional (bool): Enable enterprise professional courses
        module_openeducat_online_facility_enterprise_professional (bool): Enable enterprise professional facilities
        module_openeducat_online_library_enterprise_professional (bool): Enable enterprise professional library
        module_openeducat_online_exam_enterprise_professional (bool): Enable enterprise professional exams
        module_openeducat_online_meeting_enterprise_professional (bool): Enable enterprise professional meetings
        module_openeducat_online_timetable_enterprise_professional (bool): Enable enterprise professional timetable
        module_openeducat_online_attendance_enterprise_professional (bool): Enable enterprise professional attendance
        module_openeducat_online_assignment_enterprise_professional (bool): Enable enterprise professional assignments
        module_openeducat_online_admission_standard_professional (bool): Enable standard professional admission
        module_openeducat_online_course_standard_professional (bool): Enable standard professional courses
        module_openeducat_online_facility_standard_professional (bool): Enable standard professional facilities
        module_openeducat_online_library_standard_professional (bool): Enable standard professional library
        module_openeducat_online_exam_standard_professional (bool): Enable standard professional exams
        module_openeducat_online_meeting_standard_professional (bool): Enable standard professional meetings
        module_openeducat_online_timetable_standard_professional (bool): Enable standard professional timetable
        module_openeducat_online_attendance_standard_professional (bool): Enable standard professional attendance
        module_openeducat_online_assignment_standard_professional (bool): Enable standard professional assignments
        module_openeducat_online_admission_enterprise_standard_professional (bool): Enable enterprise standard professional admission
        module_openeducat_online_course_enterprise_standard_professional (bool): Enable enterprise standard professional courses
        module_openeducat_online_facility_enterprise_standard_professional (bool): Enable enterprise standard professional facilities
        module_openeducat_online_library_enterprise_standard_professional (bool): Enable enterprise standard professional library
        module_openeducat_online_exam_enterprise_standard_professional (bool): Enable enterprise standard professional exams
        module_openeducat_online_meeting_enterprise_standard_professional (bool): Enable enterprise standard professional meetings
        module_openeducat_online_timetable_enterprise_standard_professional (bool): Enable enterprise standard professional timetable
        module_openeducat_online_attendance_enterprise_standard_professional (bool): Enable enterprise standard professional attendance
        module_openeducat_online_assignment_enterprise_standard_professional (bool): Enable enterprise standard professional assignments
        attendance_subject_generic (str): Attendance collection method
    """

    _inherit = 'res.config.settings'

    # Core Modules
    module_openeducat_activity = fields.Boolean(
        string='Activity',
        help='Enable activity tracking and management'
    )
    module_openeducat_facility = fields.Boolean(
        string='Facility',
        help='Enable facility management and booking'
    )
    module_openeducat_exam = fields.Boolean(
        string='Exam',
        help='Enable examination management and grading'
    )
    module_openeducat_timetable = fields.Boolean(
        string='Timetable',
        help='Enable timetable management and scheduling'
    )
    module_openeducat_library = fields.Boolean(
        string='Library',
        help='Enable library management and book tracking'
    )
    module_openeducat_transportation = fields.Boolean(
        string='Transportation',
        help='Enable transportation management and routing'
    )
    module_openeducat_achievement = fields.Boolean(
        string='Achievement',
        help='Enable achievement tracking and recognition'
    )
    module_openeducat_parent = fields.Boolean(
        string='Parent',
        help='Enable parent portal and communication'
    )
    module_openeducat_discipline = fields.Boolean(
        string='Discipline',
        help='Enable discipline management and tracking'
    )
    module_openeducat_attendance = fields.Boolean(
        string='Attendance',
        help='Enable attendance tracking and reporting'
    )
    module_openeducat_health = fields.Boolean(
        string='Health',
        help='Enable health management and tracking'
    )
    module_openeducat_scholarship = fields.Boolean(
        string='Scholarship',
        help='Enable scholarship management and tracking'
    )
    module_openeducat_fees = fields.Boolean(
        string='Fees',
        help='Enable fee management and collection'
    )
    module_openeducat_admission = fields.Boolean(
        string='Admission',
        help='Enable admission management and processing'
    )
    module_openeducat_alumni = fields.Boolean(
        string='Alumni',
        help='Enable alumni management and tracking'
    )
    module_openeducat_assignment = fields.Boolean(
        string='Assignment',
        help='Enable assignment management and grading'
    )

    # Online Modules
    module_openeducat_online_admission = fields.Boolean(
        string='Online Admission',
        help='Enable online admission process'
    )
    module_openeducat_online_course = fields.Boolean(
        string='Online Course',
        help='Enable online course management'
    )
    module_openeducat_online_facility = fields.Boolean(
        string='Online Facility',
        help='Enable online facility booking'
    )
    module_openeducat_online_library = fields.Boolean(
        string='Online Library',
        help='Enable online library management'
    )
    module_openeducat_online_exam = fields.Boolean(
        string='Online Exam',
        help='Enable online examination system'
    )
    module_openeducat_online_meeting = fields.Boolean(
        string='Online Meeting',
        help='Enable online meeting management'
    )
    module_openeducat_online_timetable = fields.Boolean(
        string='Online Timetable',
        help='Enable online timetable management'
    )
    module_openeducat_online_attendance = fields.Boolean(
        string='Online Attendance',
        help='Enable online attendance tracking'
    )
    module_openeducat_online_assignment = fields.Boolean(
        string='Online Assignment',
        help='Enable online assignment management'
    )

    # Enterprise Modules
    module_openeducat_online_admission_enterprise = fields.Boolean(
        string='Online Admission Enterprise',
        help='Enable enterprise online admission'
    )
    module_openeducat_online_course_enterprise = fields.Boolean(
        string='Online Course Enterprise',
        help='Enable enterprise online courses'
    )
    module_openeducat_online_facility_enterprise = fields.Boolean(
        string='Online Facility Enterprise',
        help='Enable enterprise online facilities'
    )
    module_openeducat_online_library_enterprise = fields.Boolean(
        string='Online Library Enterprise',
        help='Enable enterprise online library'
    )
    module_openeducat_online_exam_enterprise = fields.Boolean(
        string='Online Exam Enterprise',
        help='Enable enterprise online exams'
    )
    module_openeducat_online_meeting_enterprise = fields.Boolean(
        string='Online Meeting Enterprise',
        help='Enable enterprise online meetings'
    )
    module_openeducat_online_timetable_enterprise = fields.Boolean(
        string='Online Timetable Enterprise',
        help='Enable enterprise online timetable'
    )
    module_openeducat_online_attendance_enterprise = fields.Boolean(
        string='Online Attendance Enterprise',
        help='Enable enterprise online attendance'
    )
    module_openeducat_online_assignment_enterprise = fields.Boolean(
        string='Online Assignment Enterprise',
        help='Enable enterprise online assignments'
    )

    # Standard Modules
    module_openeducat_online_admission_standard = fields.Boolean(
        string='Online Admission Standard',
        help='Enable standard online admission'
    )
    module_openeducat_online_course_standard = fields.Boolean(
        string='Online Course Standard',
        help='Enable standard online courses'
    )
    module_openeducat_online_facility_standard = fields.Boolean(
        string='Online Facility Standard',
        help='Enable standard online facilities'
    )
    module_openeducat_online_library_standard = fields.Boolean(
        string='Online Library Standard',
        help='Enable standard online library'
    )
    module_openeducat_online_exam_standard = fields.Boolean(
        string='Online Exam Standard',
        help='Enable standard online exams'
    )
    module_openeducat_online_meeting_standard = fields.Boolean(
        string='Online Meeting Standard',
        help='Enable standard online meetings'
    )
    module_openeducat_online_timetable_standard = fields.Boolean(
        string='Online Timetable Standard',
        help='Enable standard online timetable'
    )
    module_openeducat_online_attendance_standard = fields.Boolean(
        string='Online Attendance Standard',
        help='Enable standard online attendance'
    )
    module_openeducat_online_assignment_standard = fields.Boolean(
        string='Online Assignment Standard',
        help='Enable standard online assignments'
    )

    # Professional Modules
    module_openeducat_online_admission_professional = fields.Boolean(
        string='Online Admission Professional',
        help='Enable professional online admission'
    )
    module_openeducat_online_course_professional = fields.Boolean(
        string='Online Course Professional',
        help='Enable professional online courses'
    )
    module_openeducat_online_facility_professional = fields.Boolean(
        string='Online Facility Professional',
        help='Enable professional online facilities'
    )
    module_openeducat_online_library_professional = fields.Boolean(
        string='Online Library Professional',
        help='Enable professional online library'
    )
    module_openeducat_online_exam_professional = fields.Boolean(
        string='Online Exam Professional',
        help='Enable professional online exams'
    )
    module_openeducat_online_meeting_professional = fields.Boolean(
        string='Online Meeting Professional',
        help='Enable professional online meetings'
    )
    module_openeducat_online_timetable_professional = fields.Boolean(
        string='Online Timetable Professional',
        help='Enable professional online timetable'
    )
    module_openeducat_online_attendance_professional = fields.Boolean(
        string='Online Attendance Professional',
        help='Enable professional online attendance'
    )
    module_openeducat_online_assignment_professional = fields.Boolean(
        string='Online Assignment Professional',
        help='Enable professional online assignments'
    )

    # Enterprise Standard Modules
    module_openeducat_online_admission_enterprise_standard = fields.Boolean(
        string='Online Admission Enterprise Standard',
        help='Enable enterprise standard online admission'
    )
    module_openeducat_online_course_enterprise_standard = fields.Boolean(
        string='Online Course Enterprise Standard',
        help='Enable enterprise standard online courses'
    )
    module_openeducat_online_facility_enterprise_standard = fields.Boolean(
        string='Online Facility Enterprise Standard',
        help='Enable enterprise standard online facilities'
    )
    module_openeducat_online_library_enterprise_standard = fields.Boolean(
        string='Online Library Enterprise Standard',
        help='Enable enterprise standard online library'
    )
    module_openeducat_online_exam_enterprise_standard = fields.Boolean(
        string='Online Exam Enterprise Standard',
        help='Enable enterprise standard online exams'
    )
    module_openeducat_online_meeting_enterprise_standard = fields.Boolean(
        string='Online Meeting Enterprise Standard',
        help='Enable enterprise standard online meetings'
    )
    module_openeducat_online_timetable_enterprise_standard = fields.Boolean(
        string='Online Timetable Enterprise Standard',
        help='Enable enterprise standard online timetable'
    )
    module_openeducat_online_attendance_enterprise_standard = fields.Boolean(
        string='Online Attendance Enterprise Standard',
        help='Enable enterprise standard online attendance'
    )
    module_openeducat_online_assignment_enterprise_standard = fields.Boolean(
        string='Online Assignment Enterprise Standard',
        help='Enable enterprise standard online assignments'
    )

    # Enterprise Professional Modules
    module_openeducat_online_admission_enterprise_professional = fields.Boolean(
        string='Online Admission Enterprise Professional',
        help='Enable enterprise professional online admission'
    )
    module_openeducat_online_course_enterprise_professional = fields.Boolean(
        string='Online Course Enterprise Professional',
        help='Enable enterprise professional online courses'
    )
    module_openeducat_online_facility_enterprise_professional = fields.Boolean(
        string='Online Facility Enterprise Professional',
        help='Enable enterprise professional online facilities'
    )
    module_openeducat_online_library_enterprise_professional = fields.Boolean(
        string='Online Library Enterprise Professional',
        help='Enable enterprise professional online library'
    )
    module_openeducat_online_exam_enterprise_professional = fields.Boolean(
        string='Online Exam Enterprise Professional',
        help='Enable enterprise professional online exams'
    )
    module_openeducat_online_meeting_enterprise_professional = fields.Boolean(
        string='Online Meeting Enterprise Professional',
        help='Enable enterprise professional online meetings'
    )
    module_openeducat_online_timetable_enterprise_professional = fields.Boolean(
        string='Online Timetable Enterprise Professional',
        help='Enable enterprise professional online timetable'
    )
    module_openeducat_online_attendance_enterprise_professional = fields.Boolean(
        string='Online Attendance Enterprise Professional',
        help='Enable enterprise professional online attendance'
    )
    module_openeducat_online_assignment_enterprise_professional = fields.Boolean(
        string='Online Assignment Enterprise Professional',
        help='Enable enterprise professional online assignments'
    )

    # Standard Professional Modules
    module_openeducat_online_admission_standard_professional = fields.Boolean(
        string='Online Admission Standard Professional',
        help='Enable standard professional online admission'
    )
    module_openeducat_online_course_standard_professional = fields.Boolean(
        string='Online Course Standard Professional',
        help='Enable standard professional online courses'
    )
    module_openeducat_online_facility_standard_professional = fields.Boolean(
        string='Online Facility Standard Professional',
        help='Enable standard professional online facilities'
    )
    module_openeducat_online_library_standard_professional = fields.Boolean(
        string='Online Library Standard Professional',
        help='Enable standard professional online library'
    )
    module_openeducat_online_exam_standard_professional = fields.Boolean(
        string='Online Exam Standard Professional',
        help='Enable standard professional online exams'
    )
    module_openeducat_online_meeting_standard_professional = fields.Boolean(
        string='Online Meeting Standard Professional',
        help='Enable standard professional online meetings'
    )
    module_openeducat_online_timetable_standard_professional = fields.Boolean(
        string='Online Timetable Standard Professional',
        help='Enable standard professional online timetable'
    )
    module_openeducat_online_attendance_standard_professional = fields.Boolean(
        string='Online Attendance Standard Professional',
        help='Enable standard professional online attendance'
    )
    module_openeducat_online_assignment_standard_professional = fields.Boolean(
        string='Online Assignment Standard Professional',
        help='Enable standard professional online assignments'
    )

    # Enterprise Standard Professional Modules
    module_openeducat_online_admission_enterprise_standard_professional = fields.Boolean(
        string='Online Admission Enterprise Standard Professional',
        help='Enable enterprise standard professional online admission'
    )
    module_openeducat_online_course_enterprise_standard_professional = fields.Boolean(
        string='Online Course Enterprise Standard Professional',
        help='Enable enterprise standard professional online courses'
    )
    module_openeducat_online_facility_enterprise_standard_professional = fields.Boolean(
        string='Online Facility Enterprise Standard Professional',
        help='Enable enterprise standard professional online facilities'
    )
    module_openeducat_online_library_enterprise_standard_professional = fields.Boolean(
        string='Online Library Enterprise Standard Professional',
        help='Enable enterprise standard professional online library'
    )
    module_openeducat_online_exam_enterprise_standard_professional = fields.Boolean(
        string='Online Exam Enterprise Standard Professional',
        help='Enable enterprise standard professional online exams'
    )
    module_openeducat_online_meeting_enterprise_standard_professional = fields.Boolean(
        string='Online Meeting Enterprise Standard Professional',
        help='Enable enterprise standard professional online meetings'
    )
    module_openeducat_online_timetable_enterprise_standard_professional = fields.Boolean(
        string='Online Timetable Enterprise Standard Professional',
        help='Enable enterprise standard professional online timetable'
    )
    module_openeducat_online_attendance_enterprise_standard_professional = fields.Boolean(
        string='Online Attendance Enterprise Standard Professional',
        help='Enable enterprise standard professional online attendance'
    )
    module_openeducat_online_assignment_enterprise_standard_professional = fields.Boolean(
        string='Online Assignment Enterprise Standard Professional',
        help='Enable enterprise standard professional online assignments'
    )

    # Attendance Configuration
    attendance_subject_generic = fields.Selection([
        ('subject', 'Subject Wise'),
        ('generic', 'Generic')
    ], string='Attendance Collection',
        help='Choose how attendance should be collected - by subject or generically',
        default='subject'
    )
