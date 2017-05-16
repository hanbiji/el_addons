#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Walmart Order

from ..walmart import *

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class WalmartEl(models.Model):
    """Amazon conntent"""
    # access_key = 'AKIAIGLHKPMLI6WEHVYQ'
    # secret_key = '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'
    # account_id = 'A2DHO4DEH44QSX'
    # marketplaceid = 'ATVPDKIKX0DER'
    _name = 'walmart.el'
    _description = 'Walmart Manage'
    name = fields.Char(string='Store Name', required=True)
    private_key = fields.Text(string='Private Key', required=True)
    channel_type = fields.Char(string='Channel Type', required=True)
    consumer_id = fields.Char(string='Consumer Id', required=True)


