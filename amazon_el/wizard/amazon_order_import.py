# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..mws import mws

from odoo import api, fields, models, _
from datetime import datetime, timedelta
import time
from odoo.exceptions import AccessDenied
import logging
import hashlib

_logger = logging.getLogger(__name__)


class AmazonOrderImport(models.TransientModel):
    """Amazon 订单导入"""
    _name = 'amazon.order.import'
    amazon = fields.Many2one('amazon', 'Amazon', required=True)
    order_status = fields.Selection([
        ('PendingAvailability', 'PendingAvailability'),
        ('Pending', 'Pending'),
        ('Unshipped', 'Unshipped'),
        ('PartiallyShipped', 'PartiallyShipped'),
        ('Shipped', 'Shipped'),
        ('Canceled', 'Canceled'),
        ('Unfulfillable', 'Unfulfillable')
    ], default='Unshipped')
    last_updated_after = fields.Datetime('From Date', required=True)
    last_updated_before = fields.Datetime('From To')
    fulfillment_channel = fields.Selection([('AFN', 'AFN'), ('MFN', 'MFN')], string='Fulfillment Channel')

    @api.multi
    def do_order_import(self):
        """导入amazon订单"""
        self.ensure_one()
        mws_order = mws.Orders(self.amazon.access_key, self.amazon.secret_key, self.amazon.account_id,
                               self.amazon.region)
        lastupdatedafter = datetime.strptime(self.last_updated_after, '%Y-%m-%d %H:%M:%S').isoformat()
        fulfillment_channel = self.fulfillment_channel

        if self.order_status in ('Unshipped', 'PartiallyShipped'):
            orderstatus = ('Unshipped', 'PartiallyShipped')
        else:
            orderstatus = (self.order_status,)
        response = mws_order.list_orders((self.amazon.marketplace_id,), lastupdatedafter=lastupdatedafter,
                                         orderstatus=orderstatus, fulfillment_channels=(fulfillment_channel,))
        self.save_order(response.parsed['Orders']['Order'], self.amazon.id, mws_order)
        if 'NextToken' in response.parsed.keys():
            next_token = response.parsed['NextToken']['value']
            self.import_order_by_next_token(mws_order, next_token, self.amazon.id)
        dict2 = {
            'name': _('Import Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'amazon.order.import',
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

        # return dict2
        return {'type': 'ir.actions.act_window_close'}

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
    def auto_import_order(self):
        """自动导入订单"""

        yesterday = datetime.now() + timedelta(-1)
        amazons = self.env['amazon'].search([])
        for amazon_config in amazons:
            mws_order = mws.Orders(amazon_config.access_key, amazon_config.secret_key, amazon_config.account_id,
                                   amazon_config.region)
            lastupdatedafter = yesterday.isoformat()
            orderstatus = ('Unshipped', 'PartiallyShipped')
            response = mws_order.list_orders((amazon_config.marketplace_id,), lastupdatedafter=lastupdatedafter,
                                             orderstatus=orderstatus)
            self.save_order(response.parsed['Orders']['Order'], self.amazon.id, mws_order)
            if 'NextToken' in response.parsed.keys():
                next_token = response.parsed['NextToken']['value']
                self.import_order_by_next_token(mws_order, next_token, self.amazon.id)

        return True

    @api.model
    def import_order_by_next_token(self, mws_order, next_token, amazon_id):
        response = mws_order.list_orders_by_next_token(next_token)
        self.save_order(response.parsed['Orders']['Order'], amazon_id, mws_order)
        if 'NextToken' in response.parsed.keys():
            next_token = response.parsed['NextToken']['value']
            return self.import_order_by_next_token(mws_order, next_token, amazon_id)
        else:
            return True

    @api.model
    def save_order(self, orders, amazon_id, mws_order):
        for order in orders:
            OrderId = order['AmazonOrderId']['value']
            fulfillment_channel = order['FulfillmentChannel']['value']
            # CustomerName = order['BuyerName']['value']
            Email = None
            if 'BuyerEmail' in order.keys():
                Email = order['BuyerEmail']['value']
                if Email:
                    m = hashlib.md5()
                    m.update(Email)
                    Email = m.hexdigest()

            ShippingAddress = order['ShippingAddress']
            Address = ShippingAddress['AddressLine1']['value']
            Address1 = Address2 = ''
            if 'AddressLine2' in ShippingAddress.keys():
                Address1 = ShippingAddress['AddressLine2']['value']

            City = None
            if 'City' in ShippingAddress.keys():
                City = ShippingAddress['City']['value']

            State = None
            if 'StateOrRegion' in ShippingAddress.keys():
                State = ShippingAddress['StateOrRegion']['value']

            Zip = None
            if 'PostalCode' in ShippingAddress.keys():
                Zip = ShippingAddress['PostalCode']['value']

            CustomerName = ShippingAddress['Name']['value']

            Country = None
            if 'CountryCode' in ShippingAddress.keys():
                Country = ShippingAddress['CountryCode']['value']

            country_ids = self.env['res.country'].search([('code', '=', Country)])

            Phone = None
            if 'Phone' in ShippingAddress.keys():
                Phone = ShippingAddress['Phone']['value']

            # OrderTotal = order['OrderTotal']['Amount']['value']
            CurrencyCode = order['OrderTotal']['CurrencyCode']['value']
            price_list = self.env['product.pricelist'].search([('currency_id', '=', CurrencyCode)])

            Created = order['PurchaseDate']['value']
            LatestShipDate = order['LatestShipDate']['value']

            state_id = 0
            if State is not None:
                # 查询州ID
                states = self.env['res.country.state'].search([
                    ('country_id', '=', country_ids[0]['id']),
                    ('code', '=', State)
                ])

                for state in states:
                    state_id = state['id']

            # 查询用户是否存在
            search_customer = self.env['res.partner'].search([('email', '=', Email)])

            customer_id = 0
            if search_customer:
                customer_id = search_customer[0]['id']

            # 添加收货地址
            customer = {
                'type': 'delivery',
                'parent_id': customer_id,
                'name': CustomerName,
                'email': Email,
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
            customer = self.env['res.partner'].create(customer)

            customer_id = customer[0]['id']

            # 查询订单是否存在
            check_order = self.env['sale.order'].search([('client_order_ref', '=', OrderId)])

            if not check_order:
                # 新建订单
                state = 'draft'
                if fulfillment_channel == 'AFN':
                    state = 'done'
                sale = self.env['sale.order'].create({
                    'partner_id': customer_id,
                    'client_order_ref': OrderId,
                    'team_id': 4,
                    'date_order': Created,
                    'validity_date': LatestShipDate,
                    'state': state,
                    'amazon_id': amazon_id,
                    'fulfillment_channel': fulfillment_channel,
                    'amazon_order_status': order['OrderStatus']['value']
                })
                # 获取订单产品
                print "Start : %s" % time.ctime()
                time.sleep(2)
                print "End : %s" % time.ctime()
                amazon_order_id = OrderId
                order_items = mws_order.list_order_items(amazon_order_id)
                items = []
                if isinstance(order_items.parsed['OrderItems']['OrderItem'], list):
                    for item in order_items.parsed['OrderItems']['OrderItem']:
                        shipping_price = shipping_discount = promotion_discount = 0
                        if 'ShippingPrice' in item.keys():
                            shipping_price = float(item['ShippingPrice']['Amount']['value'])
                        if 'ShippingDiscount' in item.keys():
                            shipping_discount = float(item['ShippingDiscount']['Amount']['value'])
                        if 'PromotionDiscount' in item.keys():
                            promotion_discount = float(item['PromotionDiscount']['Amount']['value'])
                        items.append({
                            'sku': item['SellerSKU']['value'],
                            'order_item_id': item['OrderItemId']['value'],
                            'asin': item['ASIN']['value'],
                            'qty': item['QuantityOrdered']['value'],
                            'price_unit': float(item['ItemPrice']['Amount']['value']),
                            'shipping_price': shipping_price,
                            'shipping_discount': shipping_discount,
                            'promotion_discount': promotion_discount
                        })
                elif isinstance(order_items.parsed['OrderItems']['OrderItem'], dict):
                    item = order_items.parsed['OrderItems']['OrderItem']
                    shipping_price = shipping_discount = promotion_discount = 0
                    if 'ShippingPrice' in item.keys():
                        shipping_price = float(item['ShippingPrice']['Amount']['value'])
                    if 'ShippingDiscount' in item.keys():
                        shipping_discount = float(item['ShippingDiscount']['Amount']['value'])
                    if 'PromotionDiscount' in item.keys():
                        promotion_discount = float(item['PromotionDiscount']['Amount']['value'])
                    items.append({
                        'sku': item['SellerSKU']['value'],
                        'order_item_id': item['OrderItemId']['value'],
                        'asin': item['ASIN']['value'],
                        'qty': item['QuantityOrdered']['value'],
                        'price_unit': float(item['ItemPrice']['Amount']['value']),
                        'shipping_price': shipping_price,
                        'shipping_discount': shipping_discount,
                        'promotion_discount': promotion_discount
                    })

                for i in items:
                    sku = i['sku']
                    product_uom_qty = float(i['qty'])

                    default_code = sku
                    price_unit = (i['price_unit'] + i['shipping_price'] - i['shipping_discount'] - i[
                        'promotion_discount']) / product_uom_qty
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
                        'price_unit': price_unit,
                        'amazon_order_item_id': i['order_item_id']
                    })

        return True

    @api.model
    def post_order_fulfillment(self, order_id=None):
        """
        <?xml version="1.0" encoding="UTF-8"?>
            <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                <Header>
                    <DocumentVersion>1.01</DocumentVersion>
                    <MerchantIdentifier></MerchantIdentifier>
                </Header>
                <MessageType>OrderFulfillment</MessageType>
                <Message>
                    <MessageID>2</MessageID>
                    <OrderFulfillment>
                        <AmazonOrderID>113-3063592-6401803</AmazonOrderID>
                        <MerchantFulfillmentID>2</MerchantFulfillmentID>
                        <FulfillmentDate>2017-05-03T15:30:33+08:00</FulfillmentDate>
                        <FulfillmentData>
                            <CarrierCode>USPS</CarrierCode>
                            <ShippingMethod>Standard</ShippingMethod>
                            <ShipperTrackingNumber>LN259170331SG</ShipperTrackingNumber>
                        </FulfillmentData>
                        <Item>
                            <AmazonOrderItemCode>69188975460442</AmazonOrderItemCode>
                            <Quantity>1</Quantity>
                        </Item>
                    </OrderFulfillment>
                </Message>
            </AmazonEnvelope>
        """

        message_tpl = """<Message>
                    <MessageID>{MessageID}</MessageID>
                    <OrderFulfillment>
                        <AmazonOrderID>{AmazonOrderID}</AmazonOrderID>
                        <FulfillmentDate>{FulfillmentDate}</FulfillmentDate>
                        <FulfillmentData>
                            <CarrierCode>{CarrierCode}</CarrierCode>
                            <ShipperTrackingNumber>{ShipperTrackingNumber}</ShipperTrackingNumber>
                        </FulfillmentData>
                        <Item>
                            <AmazonOrderItemCode>{AmazonOrderItemCode}</AmazonOrderItemCode>
                            <Quantity>{Quantity}</Quantity>
                        </Item>
                    </OrderFulfillment>
                </Message>"""
        amazons = self.env['amazon'].search([])
        message_id = 1
        for amazon_config in amazons:
            orders = self.env['sale.order'].search(
                [('amazon_id', '=', amazon_config.id), ('amazon_order_status', '=', 'Unshipped'),
                 ('fulfillment_channel', '=', 'MFN')])
            messages = []
            for order in orders:
                items = []
                for order_line in order.order_line:
                    if order_line.amazon_order_item_id:
                        items.append({
                            'AmazonOrderItemCode': order_line.amazon_order_item_id,
                            'Quantity': int(order_line.product_uom_qty)
                        })

                stock_pickings = self.env['stock.picking'].search([('origin', '=', order.name)])
                carriers = []
                for picking in stock_pickings:
                    for track in picking.carrier_tracking_ref:
                        message_id += 1
                        carriers.append({
                            'CarrierCode': track.carrier_id.carrier_code,
                            'ShipperTrackingNumber': track.tracking_ref,
                            'MessageID': message_id
                        })
                if carriers:
                    if len(carriers) >= len(items):
                        message = ''.join([message_tpl.format(MessageID=carr['MessageID'], AmazonOrderID=order.client_order_ref,
                                                  FulfillmentDate=datetime.now().isoformat(),
                                                  CarrierCode=carr['CarrierCode'],
                                                  ShipperTrackingNumber=carr['ShipperTrackingNumber'],
                                                  AmazonOrderItemCode=item['AmazonOrderItemCode'],
                                                  Quantity=item['Quantity']) for item, carr in zip(items, carriers)])
                    else:
                        item_tpl = """<Item>
                                <AmazonOrderItemCode>{AmazonOrderItemCode}</AmazonOrderItemCode>
                                <Quantity>{Quantity}</Quantity>
                            </Item>"""
                        item_str = ''.join([item_tpl.format(AmazonOrderItemCode=item['AmazonOrderItemCode'], Quantity=item['Quantity']) for item in items])
                        message = """<Message>
                                <MessageID>{MessageID}</MessageID>
                                <OrderFulfillment>
                                    <AmazonOrderID>{AmazonOrderID}</AmazonOrderID>
                                    <FulfillmentDate>{FulfillmentDate}</FulfillmentDate>
                                    <FulfillmentData>
                                        <CarrierCode>{CarrierCode}</CarrierCode>
                                        <ShipperTrackingNumber>{ShipperTrackingNumber}</ShipperTrackingNumber>
                                    </FulfillmentData>
                                    {item}
                                </OrderFulfillment>
                            </Message>""".format(MessageID=message_id, AmazonOrderID=order.client_order_ref, FulfillmentDate=datetime.now().isoformat(), CarrierCode=carriers[0]['CarrierCode'], ShipperTrackingNumber=carriers[0]['ShipperTrackingNumber'], item=item_str)

                    messages.append(message)
                    # 更新订单状态
                    order.update({'amazon_order_status': 'Shipped'})

            # 提交FEED
            if messages:
                # 更新订单状态
                order.update({'amazon_order_status': 'Shipped'})
                feed = """<?xml version="1.0" encoding="UTF-8"?>
                    <AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
                        <Header>
                            <DocumentVersion>1.01</DocumentVersion>
                            <MerchantIdentifier></MerchantIdentifier>
                        </Header>
                        <MessageType>OrderFulfillment</MessageType>""" + ''.join(messages) + '</AmazonEnvelope>'
                # print feed
                feed_model = mws.Feeds(amazon_config.access_key, amazon_config.secret_key, amazon_config.account_id,
                                       amazon_config.region)
                response = feed_model.submit_feed(feed, '_POST_ORDER_FULFILLMENT_DATA_', (amazon_config.marketplace_id,))
                # print response.original
                # print response.parsed
                feed_id = response.parsed['FeedSubmissionInfo']['FeedSubmissionId']['value']
                submitted_date = response.parsed['FeedSubmissionInfo']['SubmittedDate']['value']
                status = response.parsed['FeedSubmissionInfo']['FeedProcessingStatus']['value']
                # 保存 FEED 提交记录
                self.env['amazon.feed'].create({
                    'amazon_profile': order.amazon_id,
                    'name': feed_id,
                    'feed_type': '_POST_ORDER_FULFILLMENT_DATA_',
                    'submitted_date': submitted_date,
                    'feed_xml': feed,
                    'status': status
                })

        return True
