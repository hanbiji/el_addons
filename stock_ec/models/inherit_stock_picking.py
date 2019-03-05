# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import zeep
import json
from odoo import models, fields, api, _
from odoo.osv.osv import except_osv
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """打包处理"""
    _inherit = 'stock.picking'

    _shipping_method = ['FEDEX_GROUND_LA', 'FEDEX_SMART_POST', 'GROUND_HOME_DELIVERY']
    _shipping_name = {'FEDEX_GROUND_LA': '联邦快递陆运-洛杉矶', 'FEDEX_SMART_POST': '联邦快递-USPS末端派送',
                     'GROUND_HOME_DELIVERY': '联邦快递-住宅派送-洛杉矶'}
    _ec_order_status = {'C': '待发货审核', 'W': '待发货', 'D': '已发货', 'H': '暂存', 'N': '异常订单',
                        'P': '问题件', 'X': '废弃'}

    # 海外仓订单编号
    # ec_order_code = fields.Char(string="EC Order Code")
    ec_order_ids = fields.One2many('ec.order', 'stock_picking_id', 'EC Order')

    @api.multi
    def ec_create_order(self):
        """
        1.验证地址
        2.获取SKU体积和重量
        3.分包操作
        4.试算物流价格
        5.生成订单
        6.更新本地海外仓订单号与物流号
        """
        self.ensure_one()
        # 海外仓API相关信息
        app_token = 'xx'
        app_key = 'xx'
        wsdl = 'http://47.52.107.98/default/svc/wsdl'
        client = zeep.Client(wsdl=wsdl)
        warehouse_code = 'USLA01'

        shipping_address = {
            "country_code": self.partner_id.country_id.code,
            "shipping_method": self._shipping_method[0],
            "consignee_name": self.partner_id.name,
            "consignee_company": "",
            "consignee_province": self.partner_id.state_id.code,
            "consignee_city": self.partner_id.city,
            "consignee_street": self.partner_id.street,
            "consignee_street1": self.partner_id.street2,
            "consignee_street2": "",
            "consignee_postcode": self.partner_id.zip,
            "consignee_areacode": "",
            "consignee_phone": self.partner_id.phone,
            "consignee_fax": "",
            "consignee_email": "",
            "consignee_doorplate": ""
        }
        ec_data = client.service.callService(paramsJson=json.dumps(shipping_address), appToken=app_token, appKey=app_key,
                                             service='checkAddress')
        ec_data = json.loads(ec_data)
        if ec_data['ask'] == 'Success' and ec_data['message'] == 'Success':
            reference_no = 0
            for item in self.pack_operation_product_ids:
                params = {
                    "pageSize": 100,
                    "page": 1,
                    "product_sku": item.product_id.default_code,
                    "product_sku_arr": [],
                    "warehouse_code": "",
                    "warehouse_code_arr": []
                }
                data = client.service.callService(paramsJson=json.dumps(params), appToken=app_token, appKey=app_key,
                                                  service='getProductList')
                product = json.loads(data)
                shipping_price = 0
                shipping_method = ''
                for method in self._shipping_method:
                    params = {
                        "warehouse_code": "USLA01",
                        "country_code": self.partner_id.country_id.code,
                        'postcode': self.partner_id.zip,
                        "shipping_method": method,
                        "weight": product['data'][0]['product_weight'],
                        'length': product['data'][0]['product_length'],
                        'width': product['data'][0]['product_width'],
                        'height': product['data'][0]['product_height']
                    }
                    data = client.service.callService(paramsJson=json.dumps(params), appToken=app_token, appKey=app_key,
                                                      service='getCalculateFee')
                    data = json.loads(data)
                    if data['ask'] == 'Success':
                        if shipping_price == 0:
                            shipping_price = data['data']['totalFee']
                            shipping_method = method
                        elif data['data']['totalFee'] < shipping_price:
                            shipping_price = data['data']['totalFee']
                            shipping_method = method
                if reference_no == 0:
                    reference_no_code = self.origin
                else:
                    reference_no_code = "%s-%s" % (self.origin, reference_no)
                reference_no = reference_no + 1
                shipping_order = {
                    'reference_no': reference_no_code,
                    'shipping_method': shipping_method,
                    'warehouse_code': warehouse_code,
                    'country_code': shipping_address['country_code'],
                    'province': shipping_address['consignee_province'],
                    'city': shipping_address['consignee_city'],
                    'address1': shipping_address['consignee_street'],
                    'address2': shipping_address['consignee_street2'],
                    'zipcode': shipping_address['consignee_postcode'],
                    'name': shipping_address['consignee_name'],
                    'phone': shipping_address['consignee_phone'],
                    'verify': 1,
                    'items': [
                        {
                            "product_sku": product['data'][0]['product_sku'],
                            "product_name_en": product['data'][0]['product_declared_name'],
                            "product_declared_value": product['data'][0]['product_declared_value'],
                            "quantity": item.qty_done
                        }
                    ]
                }
                data = client.service.callService(paramsJson=json.dumps(shipping_order), appToken=app_token, appKey=app_key,
                                                  service='createOrder')
                self.message_post(body=data)
                ec_data = json.loads(data)
                # EC订单信息保存到本地
                self.env['ec.order'].create({
                    'stock_picking_id': self.id,
                    'ec_order_code': ec_data['order_code'],
                    'ec_reference_no': self.origin,
                    'ec_order_status': self._ec_order_status[ec_data['order_status']],
                    'ec_shipping_method': self._shipping_name[shipping_method],
                    'ec_warehouse_code': warehouse_code
                })
                # raise except_osv(_(u'Warning!'), data)
        else:
            raise except_osv(_(u'Warning!'), ec_data['message'])
        return True

