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
        return True

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

            customer_id = customer_id[0]['id']

            # 查询订单是否存在
            check_order = self.env['sale.order'].search([('client_order_ref', '=', OrderId)])

            if not check_order:
                # 新建订单
                sale = self.env['sale.order'].create({
                    'partner_id': customer_id,
                    'client_order_ref': OrderId,
                    'team_id': 4,
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
                        sku = 'coupon'
                        product_uom_qty = 1

                    default_code = sku
                    price_unit = float(i.find('Price').text)
                    # 产品
                    product = self.env['product.product'].search_read(
                        domain=[('default_code', '=', default_code)],
                        limit=1,
                        fields=['id', 'name', 'uom_id']
                    )
                    if not product:
                        self.create_product(default_code)
                        product = self.env['product.product'].search_read(
                            domain=[('default_code', '=', default_code)],
                            limit=1,
                            fields=['id', 'name', 'uom_id']
                        )

                    # 添加订单产品
                    self.env['sale.order.line'].create({
                        'order_id': sale[0]['id'],
                        'product_id': product[0]['id'],
                        'name': product[0]['name'],
                        'product_uom': product[0]['uom_id'][0],
                        'product_uom_qty': product_uom_qty,
                        'price_unit': price_unit
                    })

        return True
