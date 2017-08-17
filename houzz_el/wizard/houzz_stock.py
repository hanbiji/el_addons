# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..models.houzzApi import *

from odoo import api, fields, models
import math
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HouzzStock(models.TransientModel):
    """库存同步"""
    _name = 'houzz.stock'
    houzz = fields.Many2one('houzz.config', 'Houzz', required=True)
    start = fields.Integer('Start Page', default=0)

    @api.multi
    def do_update_stock(self):
        """同步库存"""
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz.houzz_token, user_name=self.houzz.houzz_user_name, app_name=self.houzz.name)
        Status = 'Active'
        listings = houzz.get_listings(Start=0, Status=Status)
        totalListingCount = float(listings['TotalListingCount'])
        counts = int(math.ceil(totalListingCount / 100.00))
        fp = file('/home/odoo/pu_not_found_sku.txt', 'w+')
        for i in range(self.start, counts):
            start = i * 100
            listings = houzz.get_listings(Start=start, Status=Status)
            if 'Listings' not in listings.keys():
                return True
            _logger.info(i)
            _logger.info(len(listings['Listings']))
            for houzz_product in listings['Listings']:
                sku = houzz_product['SKU'].upper()
                # _logger.info('%s stock is %s' % (sku, houzz_product['Quantity']))
                product = self.env['product.product'].search([('default_code', '=', sku)])
                if not product:
                    sku_box = self.env['sku.box'].search([('sku', '=', sku)])
                    if sku_box:
                        product = self.env['product.product'].search([('id', '=', sku_box[0]['product_id'].id)])
                if product:
                    qty = 0
                    quant = self.env['stock.quant'].search([('product_id', '=', product[0]['id'])])
                    for q in quant:
                        qty += q['qty']
                    if qty == 0:
                        qty = 100
                    if qty == int(houzz_product['Quantity']):
                        continue
                    update = houzz.update_inventory(sku, qty)
                    if qty < 100:
                        houzz.update_listing_shipping_details(houzz_product['SKU'])
                    else:
                        houzz.update_listing_shipping_details(houzz_product['SKU'], 7, 35)
                    _logger.info('Update Stock For %s Is %f . %s' % (sku, qty, update))
                else:
                    fp.write(sku)
                    fp.write("\r\n")
                    _logger.info('Not Found SKU:%s' % sku)
        fp.close()
        return True

    @api.model
    def cron_update_stock(self):
        """同步库存自动任务"""
        houzz_configs = self.env['houzz.config'].search([])
        for hcf in houzz_configs:
            _logger.info(hcf.name)
            _logger.info('=' * 100)

            houzz = HouzzApi(token=hcf.houzz_token, user_name=hcf.houzz_user_name, app_name=hcf.name)
            Status = 'Active'
            listings = houzz.get_listings(Start=0, Status=Status)
            totalListingCount = float(listings['TotalListingCount'])
            counts = int(math.ceil(totalListingCount / 100.00))
            fp = file('/home/odoo/' + hcf.name + '_not_found_sku.txt', 'w+')
            for i in range(counts):
                start = i * 100
                listings = houzz.get_listings(Start=start, Status=Status)
                if 'Listings' not in listings.keys():
                    return True
                _logger.info(i)
                _logger.info(len(listings['Listings']))
                for houzz_product in listings['Listings']:
                    sku = houzz_product['SKU'].upper()
                    # _logger.info('%s stock is %s' % (sku, houzz_product['Quantity']))
                    product = self.env['product.product'].search([('default_code', '=', sku)])
                    if not product:
                        sku_box = self.env['sku.box'].search([('sku', '=', sku)])
                        if sku_box:
                            product = self.env['product.product'].search([('id', '=', sku_box[0]['product_id'].id)])

                    if product:
                        qty = 0
                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', product[0]['id']), ('location_id.usage', '=', 'internal')])
                        for q in quant:
                            qty += q['qty']
                        if qty <= 2:
                            qty = 100
                        if qty == int(houzz_product['Quantity']):
                            continue
                        update = houzz.update_inventory(sku, qty)
                        if qty < 100:
                            houzz.update_listing_shipping_details(houzz_product['SKU'])
                        else:
                            houzz.update_listing_shipping_details(houzz_product['SKU'], 7, 35)
                            _logger.info('Update Stock For %s Is %f . %s' % (sku, qty, update))
                    else:
                        fp.write(sku)
                        fp.write("\r\n")
                        _logger.info('Not Found SKU:%s' % sku)
            fp.close()
        return True

    @api.model
    def test_stock(self, *args):
        """测试"""
        _logger.info(args)
        for sku in args:
            sku = sku.upper()
            # sku = 'BH13812110V'
            # _logger.info('%s stock is %s' % (sku, houzz_product['Quantity']))
            product = self.env['product.product'].search_read([('default_code', '=', sku)])
            if not product:
                sku_box = self.env['sku.box'].search([('sku', '=', sku)])
                if sku_box:
                    product = self.env['product.product'].search_read([('id', '=', sku_box[0]['product_id'].id)])
            if product:
                _logger.info('%s id: %d' % (sku, product[0]['id']))
                _logger.info(product[0]['uom_id'])
                quant = self.env['stock.quant'].search(
                    [('product_id', '=', product[0]['id']), ('location_id.usage', '=', 'internal')])
                for q in quant:
                    _logger.info(q['qty'])
            else:
                _logger.info('Not Found')
