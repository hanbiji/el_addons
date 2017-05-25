#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import base64
import time
import json
from uuid import uuid4
from urllib import urlencode
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

__all__ = [
    'WalmartItems',
    'WalmartOrder'
]


class Walmart(object):
    """Walmart api"""

    def __init__(self, consumer_id, private_key, channel_type, accept='application/xml'):
        self.base_url = 'https://marketplace.walmartapis.com/v2/%s'
        self.consumer_id = consumer_id
        self.private_key = private_key
        self.channel_type = channel_type
        self.session = requests.Session()
        self.session.headers['Accept'] = accept
        self.session.headers['WM_SVC.NAME'] = 'Walmart Marketplace'
        self.session.headers['WM_CONSUMER.ID'] = self.consumer_id
        self.session.headers['WM_CONSUMER.CHANNEL.TYPE'] = self.channel_type
        # self.session.headers['Content-Type'] = content_type

    def get_sign(self, url, method, timestamp):
        return self.sign_data(
            '\n'.join([self.consumer_id, url, method, timestamp]) + '\n',
        )

    def sign_data(self, data):
        rsakey = RSA.importKey(self.private_key.decode('base64'))
        signer = PKCS1_v1_5.new(rsakey)
        digest = SHA256.new()
        digest.update(data.encode('utf-8'))
        sign = signer.sign(digest)
        return base64.b64encode(sign)

    def get_headers(self, url, method):
        timestamp = str(int(round(time.time() * 1000)))
        return {
            'WM_SEC.AUTH_SIGNATURE': self.get_sign(url, method, timestamp),
            'WM_SEC.TIMESTAMP': timestamp,
            'WM_QOS.CORRELATION_ID': str(uuid4()),
        }

    def send_request(self, uri, method, params=None, body=None, files=None, base_url=None, next_cursor=None,
                     accept=None, content_type=None):
        if accept:
            self.session.headers['Accept'] = accept

        if content_type:
            self.session.headers['Content-Type'] = content_type
        else:
            if 'Content-Type' in self.session.headers.keys():
                del self.session.headers['Content-Type']
        if base_url:
            self.base_url = base_url
        request_url = self.base_url % uri
        if next_cursor:
            request_url += next_cursor
        else:
            if params:
                for i, r in params.items():
                    if r is None:
                        del params[i]
            if params:
                request_url += '?%s' % urlencode(params)
        # print request_url
        headers = self.get_headers(request_url, method)
        if method == 'GET':
            return self.session.get(request_url, headers=headers)
        elif method == 'PUT':
            return self.session.put(request_url, data=body, headers=headers)
        elif method == 'POST':
            return self.session.post(request_url, data=body, files=files, headers=headers)


class WalmartItems(Walmart):
    """Walmart Items
    """

    def analyze_xml(self, xml):
        ns = {
            'ns2': 'http://walmart.com/'
        }
        tree = ET.ElementTree(ET.fromstring(xml.encode('utf-8')))
        xml_root = tree.getroot()
        sub_list = xml_root.getchildren()
        data = dict()
        if 'errors' in xml_root.tag:
            error = dict()
            for i in sub_list:
                # print i.tag, i.attrib
                error['error_desc'] = i.find('description').text
                error['error_info'] = i.find('info').text
                error['error_code'] = i.find('code').text
                error['code'] = 'error'
            data.update(error)
        else:
            data.update({
                'code': 'success',
                'list': []
            })
            items = xml_root.findall('ns2:ItemResponse', ns)
            for item in items:
                sku = item.find('ns2:sku', ns).text
                data['list'].append(sku)

        return data

    def get_items(self, limit=None, offset=None, sku=None):
        self.base_url = 'https://marketplace.walmartapis.com/v3/%s'
        response = self.send_request('items', 'GET', params={'limit': limit, 'offset': offset, 'sku': sku})
        return self.analyze_xml(response.text)


class WalmartOrder(Walmart):
    """Walmart Order V3"""
    base_url = 'https://marketplace.walmartapis.com/v3/%s'

    def analyze_order(self, xml):
        """解析返回的XML"""
        # print xml
        ns = {
            'ns2': 'http://walmart.com/mp/orders',
            'ns3': 'http://walmart.com/mp/v3/orders',
            'ns4': 'http://walmart.com/'
        }
        tree = ET.ElementTree(ET.fromstring(xml.encode('utf-8')))
        xml_root = tree.getroot()
        sub_list = xml_root.getchildren()
        data = dict()

        if 'errors' in xml_root.tag:
            error = dict()
            for i in sub_list:
                # print i.tag, i.attrib
                error['error_desc'] = i.find('ns4:description', ns).text
                error['error_info'] = i.find('ns4:info', ns).text
                error['error_code'] = i.find('ns4:code', ns).text
                error['code'] = 'error'
            data.update(error)
        else:
            meta = xml_root.find('ns3:meta', ns)
            total_count = int(meta.find('ns3:totalCount', ns).text)
            limit = int(meta.find('ns3:limit', ns).text)
            next_cursor = None
            if meta.find('ns3:nextCursor', ns) is not None:
                next_cursor = meta.find('ns3:nextCursor', ns).text
            data.update({
                'code': 'success',
                'next_cursor': next_cursor,
                'total_count': total_count,
                'limit': limit,
                'list': []
            })

            elements = xml_root.find('ns3:elements', ns)
            orders = elements.findall('ns3:order', ns)
            for order in orders:
                order_info = dict()
                order_id = order.find('ns3:purchaseOrderId', ns).text
                customer_email = order.find('ns3:customerEmailId', ns).text
                order_date = order.find('ns3:orderDate', ns).text
                shipping_info = order.find('ns3:shippingInfo', ns)
                ship_date = shipping_info.find('ns3:estimatedShipDate', ns).text
                phone = shipping_info.find('ns3:phone', ns).text
                post_address = shipping_info.find('ns3:postalAddress', ns)
                name = post_address.find('ns3:name', ns).text
                address1 = post_address.find('ns3:address1', ns).text
                address2 = ''
                if post_address.find('ns3:address2', ns):
                    address2 = post_address.find('ns3:address2', ns).text
                city = post_address.find('ns3:city', ns).text
                state = post_address.find('ns3:state', ns).text
                post_code = post_address.find('ns3:postalCode', ns).text
                country = post_address.find('ns3:country', ns).text
                order_info = {
                    'order_id': order_id,
                    'customer_email': customer_email,
                    'order_date': order_date,
                    'ship_date': ship_date,
                    'phone': phone,
                    'name': name,
                    'address1': address1,
                    'address2': address2,
                    'city': city,
                    'state': state,
                    'post_code': post_code,
                    'country': country
                }

                order_lines = order.findall('ns3:orderLines/ns3:orderLine', ns)
                order_items = []
                status = ''
                for line in order_lines:
                    order_item = dict()
                    qty = float(line.find('ns3:orderLineQuantity/ns3:amount', ns).text)
                    sku = line.find('ns3:item/ns3:sku', ns).text
                    charges = line.findall('ns3:charges/ns3:charge', ns)
                    product_amount = 0.00
                    currency = ''
                    for charge in charges:
                        # print charge.find('ns3:chargeType', ns).text
                        charge_amount = charge.find('ns3:chargeAmount', ns)
                        currency = charge_amount.find('ns3:currency', ns).text
                        amount = float(charge_amount.find('ns3:amount', ns).text)
                        # TAX
                        if charge.find('ns3:tax', ns):
                            tax = float(charge.find('ns3:tax/ns3:taxAmount/ns3:amount', ns).text)
                            amount += tax
                        product_amount += amount

                    status = line.find('ns3:orderLineStatuses/ns3:orderLineStatus/ns3:status', ns).text
                    line_number = line.find('ns3:lineNumber', ns).text
                    order_item = {
                        'sku': sku,
                        'qty': qty,
                        'price': product_amount,
                        'currency': currency,
                        'line_number': line_number
                    }
                    order_items.append(order_item)
                order_info['status'] = status
                order_info['items'] = order_items
                data['list'].append(order_info)

        return data

    def get_released(self, start_date, limit=None, next_cursor=None):
        """Get Released Order"""
        params = {'createdStartDate': start_date, 'limit': limit}
        r = self.send_request(uri='orders/released', method='GET', params=params, base_url=WalmartOrder.base_url,
                              next_cursor=next_cursor)
        return self.analyze_order(r.text)

    def get_all(self, start_date, status='Created', limit=200, next_cursor=None, **kwargs):
        """Get All Orders"""
        params = {
            'createdStartDate': start_date,
            'status': status,
            'limit': limit
        }
        r = self.send_request(uri='orders', method='GET', params=params, base_url=WalmartOrder.base_url,
                              next_cursor=next_cursor)
        return self.analyze_order(r.text)

    def get_one(self, order_id):
        """Get one order"""
        r = self.send_request(uri='orders', method='GET', params={'purchaseOrderId': order_id},
                              base_url=WalmartOrder.base_url)
        return self.analyze_order(r.text)

    def acknowledge(self, order_id):
        """Acknowledging orders"""
        r = self.send_request(uri='orders/%s/acknowledge' % order_id, method='POST', accept='application/json',
                              content_type='application/json')
        order = json.loads(r.text)
        if 'errors' in order.keys():
            return {'code': 'error', 'error_code': order['errors']['error'][0]['code']}
        else:
            return {'code': 'success'}

    def shipping(self, order_id, body):
        """Shipping notifications/updates"""
        r = self.send_request(uri='orders/%s/shipping' % order_id, method='POST', body=body, accept='application/json',
                              content_type='application/json')

        print r.text
        order = json.loads(r.text)
        if 'errors' in order.keys() or 'error' in order.keys():
            return {'code': 'error', 'error_code': order['errors']['error'][0]['code']}
        else:
            return {'code': 'success'}


class WalmartInventory(Walmart):
    """Walmart Inventory
    Version: V2
    """

    def analyze_xml(self, xml):
        ns = {
            'ns2': 'http://walmart.com/'
        }
        tree = ET.ElementTree(ET.fromstring(xml.encode('utf-8')))
        xml_root = tree.getroot()
        sub_list = xml_root.getchildren()
        data = dict()
        if 'errors' in xml_root.tag:
            error = dict()
            for i in sub_list:
                # print i.tag, i.attrib
                error['error_desc'] = i.find('description', ns).text
                error['error_info'] = i.find('info', ns).text
                error['error_code'] = i.find('code', ns).text
                error['code'] = 'error'
            data.update(error)
        else:
            data.update({
                'code': 'success',
                'list': []
            })

            sku = xml_root.find('ns2:sku', ns).text
            quantity = xml_root.find('ns2:quantity/ns2:amount', ns).text
            fulfillment_lag_time = xml_root.find('ns2:fulfillmentLagTime', ns).text
            data['list'].append({
                'sku': sku,
                'quantity': quantity,
                'fulfillmentLagTime': fulfillment_lag_time
            })

        return data

    def get_inventory(self, sku):
        """Get inventory for an item """
        response = self.send_request(uri='inventory?sku=%s' % sku, method='GET')
        return self.analyze_xml(response.text)

    def update_inventory(self, sku, qty, fulfillment_lag_time):
        """Update inventory for an item"""
        request_body = """
            <wm:inventory xmlns:wm="http://walmart.com/">
                <wm:sku>{sku}</wm:sku>
                <wm:quantity>
                    <wm:unit>EACH</wm:unit>
                    <wm:amount>{qty}</wm:amount>
                </wm:quantity>
                <wm:fulfillmentLagTime>{fulfillment}</wm:fulfillmentLagTime>
            </wm:inventory>
            """.format(sku=sku, qty=qty, fulfillment=fulfillment_lag_time)
        response = self.send_request(uri='inventory?sku=%s' % sku, method='PUT', body=request_body)
        return self.analyze_xml(response.text)

    def update_bulk_inventory(self, bulks):
        """Update bulk inventory
        :param bulks = [{'sku': 'CYJJ002', 'qty': 38, 'fulfillment': 10}]
        :rtype {
                'code': 'success',
                'list': [{'feed_id': String}]
            }
        """

        max_items = 2000
        if len(bulks) > max_items:
            return {'code': 'error',
                    'error_desc': 'Up to 2,000 items can have their inventory updated in bulk in any one feed.'}

        inventory_tpl = """
            <inventory>
                <sku>{sku}</sku>
                  <quantity>
                      <unit>EACH</unit>
                      <amount>{qty}</amount>
                  </quantity>
                <fulfillmentLagTime>{fulfillment}</fulfillmentLagTime>
            </inventory>
            """
        bulk_list = [inventory_tpl.format(sku=bulk['sku'], qty=bulk['qty'], fulfillment=bulk['fulfillment']) for bulk in
                     bulks]
        bulk_data = """<?xml version="1.0" encoding="UTF-8"?>
            <InventoryFeed xmlns="http://walmart.com/">
                <InventoryHeader>
                    <version>1.4</version>
                </InventoryHeader>""" + ''.join(bulk_list) + '</InventoryFeed>'

        response = self.send_request(uri='feeds?feedType=inventory', method='POST', files={'file': bulk_data},
                                     content_type='multipart/form-data;')
        ns = {
            'ns2': 'http://walmart.com/'
        }
        tree = ET.ElementTree(ET.fromstring(response.text.encode('utf-8')))
        xml_root = tree.getroot()
        sub_list = xml_root.getchildren()
        data = dict()
        if 'errors' in xml_root.tag:
            error = dict()
            for i in sub_list:
                # print i.tag, i.attrib
                error['error_desc'] = i.find('description', ns).text
                error['error_info'] = i.find('info', ns).text
                error['error_code'] = i.find('code', ns).text
                error['code'] = 'error'
            data.update(error)
        else:
            data.update({
                'code': 'success',
                'list': []
            })

            feed_id = xml_root.find('ns2:feedId', ns).text
            data['list'].append({
                'feed_id': feed_id
            })

        return data
