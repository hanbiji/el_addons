# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..models.houzzApi import *

from odoo import api, fields, models
import math
from datetime import datetime, timedelta
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger(__name__)


class HouzzStock(models.TransientModel):

    """库存同步"""
    _name = 'houzz.stock'
    houzz = fields.Many2one('houzz.config', 'Houzz', required=True)

    @api.multi
    def do_update_stock(self):
        """同步库存"""
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz.houzz_token, user_name=self.houzz.houzz_user_name, app_name=self.houzz.name)
        Status = 'Active'
        listings = houzz.get_listings(Start=0, Status=Status)
        totalListingCount = float(listings['TotalListingCount'])
        counts = int(math.ceil(totalListingCount / 100.00))
        for i in range(counts):
            start = i * 100
            if i > 0:
                listings = houzz.get_listings(Start=start, Status=Status)
            for list in listings['Listings']:
                sku = list['SKU']
                _logger.info('%s stock is %s' % (sku, list['Quantity']))
                product = self.env['product.product'].search([('default_code', '=', sku)])
                if product:
                    qty = 0
                    quant = self.env['stock.quant'].search([('product_id', '=', product[0]['id'])])
                    for q in quant:
                        qty += q['qty']
                    update = houzz.update_inventory(sku, qty)
                    _logger.info(update)
                return True

        return True






