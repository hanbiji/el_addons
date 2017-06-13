#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Amazon Order

from zeep import Client

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class Fourpx(models.Model):
    """
    4px API配置
    """
    _name = 'four.px'

    name = fields.Char('Account')
    token = fields.Char('Token')
    order_api = fields.Char('Order API')
    order_tool_api = fields.Char('Order Tool API')








