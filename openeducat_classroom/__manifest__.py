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

{
    # Module Information
    'name': 'OpenEduCat Classroom',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'category': 'Education',
    'sequence': 3,
    'summary': 'Manage Classroom',
    'complexity': "easy",
    'author': 'OpenEduCat Inc',
    'website': 'https://www.openeducat.org',
    
    # Dependencies
    'depends': [
        'openeducat_core',
        'openeducat_facility',
        'product',
    ],
    
    # Data Files
    'data': [
        # Security
        'security/op_classroom_security.xml',
        'security/ir.model.access.csv',
        # Views
        'views/classroom_view.xml',
        # Menus
        'menus/op_menu.xml',
    ],
    
    # Demo Data
    'demo': [
        'demo/classroom_demo.xml',
        'demo/facility_line_demo.xml'
    ],
    
    # Assets
    'images': [
        'static/description/openeducat-classroom_banner.jpg',
    ],
    
    # Installation Options
    'installable': True,
    'auto_install': False,
    'application': True,
}
