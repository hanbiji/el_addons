# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from zeep import Client

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    carrier_tracking_ref = fields.One2many('tracking.reference', 'stock_picking_id')

    @api.multi
    def do_new_transfer(self):
        """提交订单到4PX，接收返回物流单号"""
        for pack in self:
            if pack.carrier_id:
                client = Client(wsdl=pack.carrier_id.four_px.order_api)
                partner = pack.partner_id
                order = {
                    'buyerId': partner.name,  # 买家ID
                    'cargoCode': 'P',  # 货物类型(默认：P)，参照货物类型表
                    'city': partner.city,  # 城市 【***】
                    'consigneeCompanyName': '',  # 收件人公司名称
                    'consigneeEmail': '',  # 收件人Email
                    'consigneeFax': '',  # 收件人传真号码
                    'consigneeName': partner.name,  # 收件人姓名【***】
                    'consigneePostCode': partner.zip,  # 收件人邮编
                    'consigneeTelephone': partner.phone,  # 收件人电话号码
                    # 'customerWeight': pack.shipping_weight,  # 客户自己称的重量(单位：KG)
                    'destinationCountryCode': partner.country_id.code,  # 目的国家二字代码，参照国家代码表
                    'stateOrProvince': partner.state_id.code,  # 州  /  省 【***】
                    'street': partner.street+' '+partner.street2,  # 街道【***】
                    'initialCountryCode': 'CN',  # 起运国家二字代码，参照国家代码表【***】
                    # 'insurType': '6P',  # 保险类型，参照保险类型表
                    # 'insurValue': '100',  # 保险价值(单位：USD)0 < Amount <= [10,2]
                    'orderNo': pack.origin,  # 客户订单号码，由客户自己定义【***】
                    'orderNote': '',  # 订单备注信息
                    'paymentCode': 'P',  # 付款类型(默认：P)，参照付款类型表
                    'pieces': '1',  # 货物件数(默认：1) 0 < Amount <= [10,2]
                    'productCode': pack.carrier_id.product_code,  # 产品代码，指DHL、新加坡小包挂号、联邮通挂号等，参照产品代码表 【***】
                    'returnSign': 'N',  # 小包退件标识 Y: 发件人要求退回 N: 无须退回(默认)
                    'shipperAddress': '3RD 12BUILDING,TONGYI QI FANG INDUSTRIAL,CAOSAN GUZHEN TOWN',  # 发件人地址
                    'shipperCompanyName': 'EILEEN GRAYS',  # 发件人公司名称
                    # 'shipperFax': '0755-29771100',  # 发件人传真号码
                    'shipperName': 'ZOUYUWEI',  # 发件人姓名
                    # 'shipperPostCode': '518000',  # 发件人邮编
                    'shipperTelephone': '18256933536',  # 发件人电话号码
                    'shipperCity': 'ZHONGSHAN',
                    'shipperStateOrProvince': 'GUANGDONG',
                    'declareInvoice': [
                        {
                            'declareNote': 'Lamp',  # 配货备注
                            'declarePieces': '1',  # 件数(默认: 1)
                            'declareUnitCode': 'PCE',  # 申报单位类型代码(默认:  PCE)，参照申报单位类型代码表
                            'eName': 'lamp',  # 海关申报英文品名
                            'name': '灯具',  # 海关申报中文品名
                            'unitPrice': '30',  # 单价 0 < Amount <= [10,2]【***】
                        }
                    ]
                }
                result = client.service.createAndPreAlertOrderService(pack.carrier_id.four_px.token, order)
                if isinstance(result, list):
                    data = result[0]
                else:
                    data = result

                if data['ack'].upper() == 'SUCCESS':
                    tracking_number = data['trackingNumber']
                    self.env['tracking.reference'].create({
                        'stock_picking_id': pack.id,
                        'tracking_ref': tracking_number,
                        'carrier_id': pack.carrier_id.id
                    })

                    return super(StockPicking, self).do_new_transfer()
                else:
                    raise UserError(data['errors'][0]['cnMessage'].encode('utf-8').decode('utf-8'))




