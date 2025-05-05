# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

###########################################################################
#
#    OpenEduCat Inc.
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
###########################################################################

import datetime
import logging
from ast import literal_eval

import requests
from odoo import api, release
from odoo.exceptions import UserError
from odoo.models import AbstractModel
from odoo.tools import misc, ustr
from odoo.tools.translate import _

# Constants
OEC_API_ENDPOINT = "https://srv.openeducat.org/publisher-warranty/"
_logger = logging.getLogger(__name__)


class PublisherWarrantyContract(AbstractModel):
    """Publisher Warranty Contract model for OpenEduCat.

    This model extends the publisher warranty contract to handle system updates
    and warranty notifications for OpenEduCat. It manages communication with
    the warranty server and collects system information for updates.

    The model provides functionality to:
    1. Collect system logs and user statistics
    2. Send update notifications to the warranty server
    3. Handle warranty contract updates
    """

    _inherit = "publisher_warranty.contract"
    _description = "Publisher Warranty Contract"

    @api.model
    def _get_message_logs(self):
        """Collect system information and user statistics.

        This method gathers various system metrics including:
        - Database information (UUID, creation date)
        - User statistics (total users, active users, share users)
        - Installed applications
        - System configuration (base URL, language)
        - Company information

        Returns:
            dict: Dictionary containing system information and statistics
        """
        Users = self.env['res.users']
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        
        # Get database information
        dbuuid = IrParamSudo.get_param('database.uuid')
        db_create_date = IrParamSudo.get_param('database.create_date')
        
        # Calculate user statistics
        limit_date = datetime.datetime.now() - datetime.timedelta(15)
        limit_date_str = limit_date.strftime(misc.DEFAULT_SERVER_DATETIME_FORMAT)
        
        nbr_users = Users.search_count([('active', '=', True)])
        nbr_active_users = Users.search_count([
            ("login_date", ">=", limit_date_str),
            ('active', '=', True)
        ])
        
        # Calculate share user statistics
        nbr_share_users = 0
        nbr_active_share_users = 0
        if "share" in Users._fields:
            nbr_share_users = Users.search_count([
                ("share", "=", True),
                ('active', '=', True)
            ])
            nbr_active_share_users = Users.search_count([
                ("share", "=", True),
                ("login_date", ">=", limit_date_str),
                ('active', '=', True)
            ])
        
        # Get installed applications
        user = self.env.user
        domain = [
            ('application', '=', True),
            ('state', 'in', ['installed', 'to upgrade', 'to remove'])
        ]
        apps = self.env['ir.module.module'].sudo().search_read(domain, ['name'])
        
        # Compile message
        msg = {
            "dbuuid": dbuuid,
            "nbr_users": nbr_users,
            "nbr_active_users": nbr_active_users,
            "nbr_share_users": nbr_share_users,
            "nbr_active_share_users": nbr_active_share_users,
            "dbname": self._cr.dbname,
            "db_create_date": db_create_date,
            "version": release.version,
            "language": user.lang,
            "web_base_url": IrParamSudo.get_param('web.base.url'),
            "apps": [app['name'] for app in apps],
        }
        
        # Add company information if available
        if user.partner_id.company_id:
            company_id = user.partner_id.company_id
            msg.update(company_id.read(["name", "email", "phone"])[0])
            
        return msg

    @api.model
    def _get_system_logs(self):
        """Send system logs to the warranty server.

        This method:
        1. Collects system information using _get_message_logs
        2. Sends the information to the warranty server
        3. Processes the server response

        Returns:
            dict: Server response containing warranty information

        Raises:
            requests.exceptions.RequestException: If communication with server fails
        """
        msg = self._get_message_logs()
        arguments = {'arg0': ustr(msg), "action": "update"}
        
        try:
            r = requests.post(OEC_API_ENDPOINT, data=arguments, timeout=30)
            r.raise_for_status()
            return literal_eval(r.text)
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to communicate with warranty server: %s", str(e))
            raise

    def update_notification_openeducat(self, cron_mode=True):
        """Update warranty notification for OpenEduCat.

        This method:
        1. Calls the parent class's update notification
        2. Attempts to send system logs to the warranty server
        3. Handles any communication errors

        Args:
            cron_mode (bool): Whether the method is called by a cron job

        Returns:
            bool: True if update was successful, False otherwise

        Raises:
            UserError: If communication with warranty server fails and not in cron mode
        """
        res = super(PublisherWarrantyContract, self).update_notification()
        
        try:
            try:
                self._get_system_logs()
            except Exception:
                if cron_mode:
                    return False
                _logger.debug(
                    "Exception while sending a get logs messages", exc_info=1)
                raise UserError(_(
                    "Error during communication with the warranty server."))
        except Exception:
            if cron_mode:
                return False
            raise
            
        return res
