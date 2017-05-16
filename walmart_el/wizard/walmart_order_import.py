# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..walmart import walmart

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import AccessDenied
import logging
import hashlib
_logger = logging.getLogger(__name__)


class WalmartElOrderImport(models.TransientModel):
    """Walmart 订单导入"""
    _name = 'walmart.el.order.import'
    walmart_el = fields.Many2one('walmart.el', 'Walmart', required=True)
    order_status = fields.Selection([
        ('Created', 'Created'),
        ('Acknowledged', 'Acknowledged'),
        ('Shipped', 'Shipped'),
        ('Cancelled', 'Cancelled')
    ], default='Created')
    last_updated_after = fields.Datetime('From Date')
    last_updated_before = fields.Datetime('From To')

    @api.multi
    def do_order_import(self):
        """Walmart"""
        self.ensure_one()
        walmart_order = walmart.WalmartOrder(self.walmart_el.consumer_id, self.walmart_el.private_key, self.walmart_el.channel_type)
        lastupdatedafter = datetime.strptime(self.last_updated_after, '%Y-%m-%d %H:%M:%S').isoformat()

        response = walmart_order.get_all(start_date=lastupdatedafter, status=self.order_status)


        if response['code'] == 'error':
            return False
        else:
            self.save_order(response['list'], self.walmart_el.id)
        dict2 = {
            'name': _('Import Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'walmart.el.order.import',
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id
        }

        # return dict2
        return True

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

    @api.multi
    def auto_import_order(self):
        """Auton import order"""
        yesterday = datetime.now() + timedelta(-1)
        for walmart_config in self.env['walmart.el'].search([]):
            walmart_order = walmart.WalmartOrder(walmart_config.consumer_id, walmart_config.private_key, walmart_config.channel_type)
            lastupdatedafter = yesterday.isoformat()
            response = walmart_order.get_all(start_date=lastupdatedafter, status='Created')
            if response['code'] == 'error':
                return False
            else:
                self.save_order(response['list'], walmart_config.id)
        return True

    @api.model
    def auto_ack(self):
        """ Auto ACK"""
        orders = self.env['sale.order'].search([('walmart_id', '!=', None), ('walmart_order_status', '=', 'Ordered')])
        _logger.info(orders)
        for order in orders:
            _logger.info(order.walmart_id.consumer_id)
            walmart_order = walmart.WalmartOrder(order.walmart_id.consumer_id, order.walmart_id.private_key,
                                                 order.walmart_id.channel_type)
            ack = walmart_order.acknowledge(order.client_order_ref)
            if ack['code']:#  == 'success'
                order.update({'walmart_order_status': 'Acknowledged'})
                order.message_post(body='Acknowledged')

    @api.model
    def save_order(self, orders, walmart_id):
        for order in orders:
            OrderId = order['order_id']
            CustomerName = order['name']
            Email = order['customer_email']
            if Email:
                m = hashlib.md5()
                m.update(Email)
                Email = m.hexdigest()

            Address = order['address1']
            Address1 = order['address2']
            City = order['city']
            State = order['state']
            Zip = order['post_code']
            Country = order['country']

            country_ids = self.env['res.country'].search([('code', '=', Country)])
            _logger.info(country_ids[0]['id'])
            Phone = order['phone']

            CurrencyCode = order['items'][0]['currency']
            price_list = self.env['product.pricelist'].search([('currency_id', '=', CurrencyCode)])

            Created = order['order_date']
            LatestShipDate = order['ship_date']

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
            search_customer = self.env['res.partner'].search([('email', '=', Email)])

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
                    'property_product_pricelist': price_list[0]['id']
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
                    'property_product_pricelist': price_list[0]['id']
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
                    'walmart_id': walmart_id,
                    'walmart_order_status': order['status']
                })
                # 订单产品
                order_items = order['items']
                for item in order_items:
                    product_uom_qty = float(item['qty'])
                    default_code = item['sku']
                    price_unit = item['price']
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


    @api.multi
    def do_update_stock(self):
        """"Update stock"""
        _logger.info('======================Update Stock===================')
        self.ensure_one()
        walmart_item = walmart.WalmartItems(self.walmart_el.consumer_id, self.walmart_el.private_key,
                                             self.walmart_el.channel_type)
        limit = 20
        i = 0
        next_items = True
        sku_list = []
        while next_items:
            offset = i * limit
            items = walmart_item.get_items(limit=limit, offset=offset)
            # _logger.info(items)
            if items['code'] == 'success':
                sku_list += items['list']
            else:
                next_items = False
            i += 1

        limit = 2000
        i = 0
        next_items = True
        walmart_inventory = walmart.WalmartInventory(self.walmart_el.consumer_id, self.walmart_el.private_key,
                                             self.walmart_el.channel_type)
        while next_items:
            offset = i * limit
            end = offset + limit
            skus = sku_list[offset:end]
            i += 1
            if skus:
                bulks_sku = self.get_bulks(skus)
                walmart_inventory.update_bulk_inventory(bulks_sku)
                # print bulks_sku
            else:
                next_items = False

        return True

    @api.model
    def get_bulks(self, skus):
        """查询库存"""
        bulks = []
        products = self.env['product.product'].search([('default_code', 'in', skus)])
        for product in products:
            sku = product['default_code']
            fulfillment = 10
            qty = 0
            quant = self.env['stock.quant'].search([('product_id', '=', product['id'])])
            for q in quant:
                qty += q['qty']
            if qty == 0:
                fulfillment = product['sale_delay'] if product['sale_delay'] > 0 else 20
                qty = 100
            bulks.append({
                'sku': sku,
                'qty': qty,
                'fulfillment': fulfillment
            })
        return bulks
