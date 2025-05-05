# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

###########################################################################
#
#    OpenEduCat Inc.
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
###########################################################################

from odoo import fields, models


class StudentPortal(models.Model):
    """Student Portal model for OpenEduCat.

    This model extends the res.partner model to add student portal functionality,
    allowing partners to be identified as students or parents in the system.

    Attributes:
        is_parent (bool): Indicates if the partner is a parent
        is_student (bool): Indicates if the partner is a student
    """

    _inherit = 'res.partner'
    _description = 'Student Portal'

    is_parent = fields.Boolean(
        string="Is a Parent",
        help="Indicates if this partner is a parent in the system",
        tracking=True
    )
    
    is_student = fields.Boolean(
        string="Is a Student",
        help="Indicates if this partner is a student in the system",
        tracking=True
    )
