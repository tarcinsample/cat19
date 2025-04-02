{
    'name': 'OpenEduCat Theme',
    'description': 'OpenEduCat Theme',
    'category': 'Theme',
    'version': '18.0.1.0',
    'author': 'OpenEduCat',
    'depends': [
        'website',
        'theme_default',
    ],
    'data': [
        'views/homepage.xml',
        'views/web.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            '/theme_web_openeducat/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            '/theme_web_openeducat/static/src/scss/style.scss',
            '/theme_web_openeducat/static/src/js/home.js',
        ],
    },
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
}
##############################################################################
