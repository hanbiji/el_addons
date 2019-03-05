# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import zeep
import json
from odoo import api, fields, models, _
from datetime import datetime
from odoo.osv.osv import except_osv
import logging

_logger = logging.getLogger(__name__)


class StockEc(models.TransientModel):
    """库存同步"""

    _name = 'stock.ec'

    @api.multi
    def create_stock_inventory(self):
        self = self.ensure_one()

        # 海外仓API相关信息
        appToken = '7b3668f184a9ab9242049c9661a61409'
        appKey = '537d1183c1472bd3d07baa4a82ecd229'
        wsdl = 'http://47.52.107.98/default/svc/wsdl'
        client = zeep.Client(wsdl=wsdl)

        # 产品库存
        params = {
            "pageSize": 100,
            "page": 1,
            "product_sku": "",
            "product_sku_arr": [],
            "warehouse_code": "",
            "warehouse_code_arr": []
        }
        ec_data = client.service.callService(paramsJson=json.dumps(params), appToken=appToken, appKey=appKey,
                                             service='getProductInventory')
        ec_data = json.loads(ec_data)

        stock_data = {
            'company_id': 1,
            'date': datetime.now(),
            'filter': 'partial',
            'location_id': 22,
            'name': u'与海外仓库存同步',
            'state': 'confirm'
        }
        inventory_id = self.env['stock.inventory'].create(stock_data)
        for ec_item in ec_data['data']:
            try:
                product_qty = int(ec_item['sellable'])
            except:
                product_qty = float(ec_item['sellable'])

            if product_qty > 0:
                product = self.env['product.product'].search_read(
                    domain=[('default_code', '=', ec_item['product_sku'])],
                    limit=1,
                    fields=['id', 'name', 'uom_id']
                )
                if product:
                    line_data = {
                        'location_id': 22,
                        'inventory_id': inventory_id.id,
                        'product_id': product[0]['id'],
                        'product_qty': product_qty,
                        'product_uom_id': 1,
                    }
                    self.env['stock.inventory.line'].create(line_data)
                else:
                    raise except_osv(_(u'Warning!'),
                                     _(u'Product %s does not exist, Please add it.') % (ec_item['product_sku']))

        return True
