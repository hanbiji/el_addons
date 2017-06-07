#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Amazon Order

from ..mws import *

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

REGION = [
    ("CA", "CA"), #A2EUQ1WTGCTBG2
    ("US", "US"), #ATVPDKIKX0DER",
    ("DE", "DE"), #A1PA6795UKMFR9
    ("ES", "ES"), #A1RKKUPIHCS9HS
    ("FR", "FR"), #A13V1IB3VIYZZH
    ("IN", "IN"), #A21TJRUUN4KGV
    ("IT", "IT"), #APJ6JRA9NG5V4
    ("UK", "UK"), #A1F83G8C2ARO7P
    ("JP", "JP"), #A1VC38T7YXB528
    ("CN", "CN"), #AAHKV2X7AFYLW
    ("MX", "MX"), #A1AM78C64UM0Y8
]


class Amazon(models.Model):
    """Amazon conntent"""
    # access_key = 'AKIAIGLHKPMLI6WEHVYQ'
    # secret_key = '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'
    # account_id = 'A2DHO4DEH44QSX'
    # marketplaceid = 'ATVPDKIKX0DER'
    _name = 'amazon'
    _description = 'Amazon conntent'
    name = fields.Char(string='Store Name', required=True)
    access_key = fields.Char(string='Access Key', required=True)
    secret_key = fields.Char(string='Secret Key', required=True)
    account_id = fields.Char(string='Account Id', required=True)
    region = fields.Selection(REGION, string='Region', required=True)
    marketplace_id = fields.Char('Marketplace Id', required=True, help="US: ATVPDKIKX0DER, CA: A2EUQ1WTGCTBG2")
    team_id = fields.Many2one('crm.team', string='Team', required=True)

