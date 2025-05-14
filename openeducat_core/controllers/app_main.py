# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

###########################################################################
#
#    OpenEduCat Inc.
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
###########################################################################

import werkzeug.utils
from odoo import http
from odoo.addons.portal.controllers.web import Home as home
from odoo.http import request


class OpeneducatHome(home):
    """OpenEduCat Home Controller.

    This controller extends the default Odoo home controller to provide
    custom login and redirection behavior for OpenEduCat users.

    The controller handles:
    1. Custom login redirection based on user type (parent/student)
    2. Portal access for parents and students
    3. Backend access for staff users
    """

    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        """Handle web login with custom redirection.

        This method:
        1. Processes the login request
        2. Determines the appropriate redirect URL based on user type:
           - Staff users -> Odoo backend
           - Parents -> Child portal
           - Students -> Student portal

        Args:
            redirect (str, optional): Custom redirect URL. Defaults to None.
            *args: Additional positional arguments
            **kw: Additional keyword arguments

        Returns:
            werkzeug.wrappers.Response: Redirect response to appropriate page
        """
        response = super(OpeneducatHome, self).web_login(
            redirect=redirect, *args, **kw)
        
        if not redirect and request.params['login_success']:
            if request.env['res.users'].browse(request.uid).has_group(
                    'base.group_user'):
                redirect = '/web?' + request.httprequest.query_string.decode('utf-8')
            else:
                if request.env.user.is_parent:
                    redirect = '/my/child'
                else:
                    redirect = '/my'
            return werkzeug.utils.redirect(redirect)
        return response

    def _login_redirect(self, uid, redirect=None):
        """Determine the redirect URL after login.

        This method:
        1. Uses the provided redirect URL if specified
        2. Otherwise, redirects based on user type:
           - Parents -> Child portal
           - Others -> Student portal

        Args:
            uid (int): User ID
            redirect (str, optional): Custom redirect URL. Defaults to None.

        Returns:
            str: Redirect URL
        """
        if redirect:
            return super(OpeneducatHome, self)._login_redirect(uid, redirect)
        if request.env.user.is_parent:
            return '/my/child'
        return '/my'
