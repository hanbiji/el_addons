# -*- coding: utf-8 -*-
# Magento

from odoo.addons.magento_el.magento import *

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class MagentoConfig(models.Model):
    """
    Magento Config
    url = 'https://www.parrotuncle.com/'
    apiuser = 'root'
    apipass = 'hbj123'
    """
    _name = 'magento.config'

    name = fields.Char('Web Site')
    url = fields.Char('Url')
    user = fields.Char('SOAP User')
    password = fields.Char('SOAP Pass', password=True)
    team_id = fields.Many2one('crm.team', string='Team', required=True)





