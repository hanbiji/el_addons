# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..models.houzzApi import *

from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger(__name__)


class HouzzOrderImport(models.TransientModel):
    """Houzz 订单导入"""

    _name = 'houzz.order.import'
    houzz = fields.Many2one('houzz.config', 'Houzz', required=True)
    order_status = fields.Selection([
        ('All', 'All'),
        ('Active', 'Active'),
        ('New', 'New'),
        ('Charged', 'Charged'),
        ('InProduction', 'InProduction'),
        ('Shipped', 'Shipped'),
        ('FailedToCharge', 'FailedToCharge')
    ], default='All')
    order_form = fields.Date('From Date')
    order_to = fields.Date('From To')
    order_limit = fields.Integer('Limit', default=1000)
    order_start = fields.Integer('Start', default=0)

    @api.multi
    def do_order_import(self):
        """导入HOUZZ订单"""
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz.houzz_token, user_name=self.houzz.houzz_user_name, app_name=self.houzz.name)
        response = houzz.get_orders(status=self.order_status, start=self.order_start, limit=self.order_limit,
                                    from_date=self.order_form, to_date=self.order_to)
        tree = ET.ElementTree(ET.fromstring(response))
        orders = tree.iter(tag='Order')
        self.save_order(orders, self.houzz.id)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def auto_import_order(self):
        """Auto import orders"""
        yesterday = datetime.now() + timedelta(-1)
        houzzs = self.env['houzz.config'].search([])
        for houzz_config in houzzs:
            houzz = HouzzApi(token=houzz_config.houzz_token, user_name=houzz_config.houzz_user_name,
                             app_name=houzz_config.name)
            response = houzz.get_orders(status='New', start=yesterday, from_date=yesterday)
            tree = ET.ElementTree(ET.fromstring(response))
            orders = tree.iter(tag='Order')
            self.save_order(orders, self.houzz.id)
        return True

    @api.model
    def process_order(self):
        """Process Order"""
        _logger.info(self)
        return True

    @api.model
    def charge_order(self, order):
        """Charge order"""
        pass

    @api.model
    def create_product(self, sku):
        """添加产品"""

        product = self.env['product.template'].create({
            'name': sku,
            'default_code': sku,
            'standard_price': 1,
            'list_price': 1,
            'image': False,
            'description_sale': False,
            'type': 'product'
        })
        for i in product:
            product_id = i['id']
        # 添加介格表
        self.env['product.pricelist.item'].create({
            'fixed_price': 1,
            'product_tmpl_id': product_id,
            'pricelist_id': 2,
            'price': 1
        })
        self.env['product.pricelist.item'].create({
            'fixed_price': 1,
            'product_tmpl_id': product_id,
            'pricelist_id': 3,
            'price': 1
        })
        # 添加供应商采购信息
        vendor = {
            'name': 14,
            'product_name': sku,
            'product_code': sku,
            'product_tmpl_id': product_id,
            'currency_id': 8,
            'price': 1,
            'min_qty': 5,
            'delay': 7
        }
        self.env['product.supplierinfo'].create(vendor)
        return True

    @api.model
    def save_order(self, orders, houzz_id):
        """Save Order"""
        for order in orders:
            OrderId = order.find('OrderId').text
            # _logger.info(OrderId)
            houzz_order_status = order.find('Status').text
            # _logger.info(houzz_order_status)
            CustomerName = order.find('CustomerName').text
            Address = order.find('Address/Address').text
            Address1 = ''
            if order.find('Address/Address1') is not None:
                Address1 = order.find('Address/Address1').text

            City = order.find('Address/City').text
            State = order.find('Address/State').text
            Zip = order.find('Address/Zip').text

            if order.find('Address/Country') is not None:
                Country = order.find('Address/Country').text
            else:
                Country = 'US'

            country_ids = self.env['res.country'].search([('code', '=', Country)])
            # _logger.info(country_ids[0]['id'])
            Phone = order.find('Address/Phone').text
            OrderTotal = float(order.find('OrderTotal').text)
            FlatShipping = float(order.find('FlatShipping').text)
            Created = order.find('Created').text
            LatestShipDate = datetime.strptime(Created, '%Y-%m-%d %H:%M:%S') + timedelta(+20)

            # 查询州ID
            state = State
            states = self.env['res.country.state'].search([
                ('country_id', '=', country_ids[0]['id']),
                ('code', '=', state)
            ])
            state_id = 0
            for state in states:
                state_id = state['id']

            # 查询用户是否存在
            search_customer = self.env['res.partner'].search([
                ('country_id', '=', country_ids[0]['id']),
                ('phone', '=', Phone)
            ])

            if search_customer:
                customer_id = search_customer[0]['id']
                # 添加收货地址
                customer = {
                    'type': 'delivery',
                    'parent_id': customer_id,
                    'name': CustomerName,
                    'email': False,
                    'phone': Phone,
                    'street': Address,
                    'street2': Address1,
                    'city': City,
                    'state_id': state_id,
                    'country_id': country_ids[0]['id'],
                    'zip': Zip,
                    'property_product_pricelist': 2
                }
                # print customer
                customer_id = self.env['res.partner'].create(customer)
            else:
                # 新建会员
                customer = {
                    'name': CustomerName,
                    'email': False,
                    'phone': Phone,
                    'street': Address,
                    'street2': Address1,
                    'city': City,
                    'state_id': state_id,
                    'country_id': country_ids[0]['id'],
                    'zip': Zip,
                    'property_product_pricelist': 2
                }
                # print customer
                customer_id = self.env['res.partner'].create(customer)

            customer_id = customer_id.id

            # 查询订单是否存在
            check_order = self.env['sale.order'].search([('client_order_ref', '=', OrderId)])

            if not check_order:
                team = self.env['houzz.config'].browse([houzz_id])
                # 新建订单
                sale = self.env['sale.order'].create({
                    'partner_id': customer_id,
                    'client_order_ref': OrderId,
                    'team_id': team.team_id.id,
                    'date_order': Created,
                    'validity_date': LatestShipDate,
                    'houzz_config_id': houzz_id,
                    'houzz_order_status': houzz_order_status
                })

                for i in order.findall('OrderItems/OrderItem'):
                    if i.find('Type').text == 'Product':
                        sku = i.find('SKU').text
                        product_uom_qty = int(i.find('Quantity').text)
                    else:
                        sku = 'COUPON'
                        product_uom_qty = 1

                    sku = sku.upper()
                    default_code = sku
                    price_unit = float(i.find('Price').text)
                    # 产品
                    product = self.env['product.product'].search_read(
                        domain=[('default_code', '=', default_code)],
                        limit=1,
                        fields=['id', 'name', 'uom_id']
                    )
                    if not product:
                        # self.create_product(default_code)
                        product = self.env['sku.box'].search_read(
                            domain=[('sku', '=', default_code)],
                            limit=1
                        )
                        if product:
                            # print product[0]['product_id']
                            product = self.env['product.product'].search_read(
                                domain=[('id', '=', product[0]['product_id'][0])],
                                limit=1,
                                fields=['id', 'name', 'uom_id']
                            )

                    if product:
                        # 添加订单内容
                        self.env['sale.order.line'].create({
                            'order_id': sale.id,
                            'product_id': product[0]['id'],
                            'name': product[0]['name'],
                            'product_uom': product[0]['uom_id'][0],
                            'product_uom_qty': product_uom_qty,
                            'price_unit': price_unit,
                            'tax_id': False
                        })
                        # 分配仓库
                        quants = self.env['stock.quant'].search([('product_id', '=', product[0]['id']),
                                                                 ('location_id.usage', '=', 'internal')])
                        for quant in quants:
                            if (quant.qty - product_uom_qty) >= 0.0:
                                warehouse = self.env['stock.warehouse'].search(
                                    [('lot_stock_id', '=', quant.location_id.id)])
                                if warehouse:
                                    sale.update({'warehouse_id': warehouse[0]['id']})
                    else:
                        sale.message_post(
                            body=u"<p style='color:red;font-size:14px'>系统没有找到SKU：%s 数量：%f, 请添加附加SKU或联系管理员</a>" % (
                                sku, product_uom_qty))

        return True

    @api.model
    def ship_order(self):
        """上传物流单号"""
        houzzs = self.env['houzz.config'].search([])
        for houzz in houzzs:
            # print houzz.houzz_token
            houzz_model = HouzzApi(token=houzz.houzz_token, user_name=houzz.houzz_user_name, app_name=houzz.name)
            orders = self.env['sale.order'].search(
                [('houzz_config_id', '=', houzz.id), ('houzz_order_status', '=', 'Charged')])
            for order in orders:
                stock_pickings = self.env['stock.picking'].search([('origin', '=', order.name)])
                carriers = []
                for picking in stock_pickings:
                    for track in picking.carrier_tracking_ref:
                        carriers.append({
                            'ShippingMethod': track.carrier_id.houzz_carrier_code,
                            'TrackingNumber': track.tracking_ref,
                        })
                if carriers:
                    track_numbers = ','.join([i['TrackingNumber'] for i in carriers])
                    shiped = houzz_model.ship_order(order_id=order.client_order_ref,
                                                    shipping_method=carriers[0]['ShippingMethod'],
                                                    tracking_number=track_numbers)
                    if shiped:
                        # 更新订单状态为Shipped
                        order.update({'houzz_order_status': 'Shipped'})

        return True


class HouzzPaymentsImport(models.TransientModel):
    """HOUZZ结算导入"""
    _name = 'houzz.payments.import'

    houzz = fields.Many2one('houzz.config', 'Houzz', required=True)
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    @api.multi
    def do_import(self):
        """Do Import Payments"""
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz.houzz_token, user_name=self.houzz.houzz_user_name, app_name=self.houzz.name)
        payment_ids = houzz.get_payments(from_date=self.from_date, to_date=self.to_date)
        for payment_id in payment_ids:
            payment = houzz.get_transactions(payment_id)
            payment_data = self.env['houzz.payments'].search_count([('payment_id', '=', payment_id)])
            if payment_data == 0:
                self.env['houzz.payments'].create({
                    'houzz_config_id': self.houzz.id,
                    'name': payment_id + 'Payment',
                    'payment_id': payment_id,
                    'from_date': payment['FromDate'],
                    'to_date': payment['ToDate'],
                    'sales': float(payment['Sales']),
                    'shipping': float(payment['Shipping']),
                    'tax': float(payment['Tax']),
                    'commission': float(payment['Commission']),
                    'deposit_amount': float(payment['DepositAmount']),
                    'currency_id': 3,
                })


