# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
import psycopg2

import odoo.addons.decimal_precision as dp

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, except_orm


class ProductTemplate(models.Model):
    """扩展产品模块，增加长，宽，高"""
    _inherit = ['product.template']

    length = fields.Float('Length', size=10)
    width = fields.Float('Width', size=10)
    height = fields.Float('Height', size=10)

