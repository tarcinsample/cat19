{
    'name': 'Charge ERP Core',
    'version': '1.0',
    'summary': 'Core module for Charge ERP',
    'description': """
        This is the core module for the Charge ERP system.
    """,
    'author': 'Jules',
    'website': 'https://www.charge-erp.com',
    'category': 'Education',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'views/student_views.xml',
        'views/course_views.xml',
        'views/faculty_views.xml',
        'views/subject_views.xml',
        'views/batch_views.xml',
        'views/program_level_views.xml',
        'views/program_views.xml',
    ],
    'installable': True,
    'application': False,
}