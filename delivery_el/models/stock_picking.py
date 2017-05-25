# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    carrier_tracking_ref = fields.One2many('tracking.reference', 'stock_picking_id')