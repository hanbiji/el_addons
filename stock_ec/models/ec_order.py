# -*- coding: utf-8 -*-

import zeep,json
from odoo import models, fields, api


class EcOrder(models.Model):
    """海外仓订单信息"""
    _name = 'ec.order'
    _rec_name = 'ec_order_code'

    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', required=True)
    ec_order_code = fields.Char(string="Order Code", required=True)
    ec_reference_no = fields.Char(string="Reference No")
    ec_order_status = fields.Char(string="Order Status")
    ec_shipping_method = fields.Char(string="Shipping Method")
    ec_tracking_no = fields.Char(string="Tracking No")
    ec_warehouse_code = fields.Char(string="Warehouse Code")
    ec_order_weight = fields.Float('Weight', (6, 2))
    ec_order_desc = fields.Text('Desc')
    ec_date_release = fields.Datetime('Release Time')
    ec_date_shipping = fields.Datetime('Shipping Time')
    ec_fee = fields.Float('Fee', (8, 2))
    ec_currency = fields.Char('Currency')

    @api.model
    def auto_update_order(self):
        """自动更新海外仓库发货单状态与tracking number"""
        # 海外仓API相关信息
        app_token = 'xx'
        app_key = 'xx'
        wsdl = 'http://47.52.107.98/default/svc/wsdl'
        client = zeep.Client(wsdl=wsdl)
        warehouse_code = 'USLA01'
        orders = self.env['ec.order'].search([('ec_tracking_no', '=', False)])

        for order in orders:
            params = {
                'order_code': order.ec_order_code
            }
            ec_data = client.service.callService(paramsJson=json.dumps(params), appToken=app_token, appKey=app_key,
                                                 service='getOrderByCode')
            ec_data = json.loads(ec_data)
            if ec_data['ask'] == 'Success' and ec_data['data']['tracking_no'] != '':
                order.ec_tracking_no = ec_data['data']['tracking_no']
                order.ec_fee = ec_data['data']['fee_details']['totalFee']
                order.ec_currency = ec_data['data']['currency']
                order.ec_date_shipping = ec_data['data']['date_shipping']
                order.ec_order_weight = ec_data['data']['order_weight']
        return True

