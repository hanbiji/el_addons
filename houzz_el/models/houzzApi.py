#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class HouzzApi(object):
    """Houzz api"""

    def __init__(self, token, user_name, app_name):
        self.token = token
        self.user_name = user_name
        self.app_name = app_name
        self.api_url = 'https://api.houzz.com/api?'
        self.session = requests.Session()
        self.session.headers['X-HOUZZ-API-SSL-TOKEN'] = token
        self.session.headers['X-HOUZZ-API-USER-NAME'] = user_name
        self.session.headers['X-HOUZZ-API-APP-NAME'] = app_name

    def get(self, url):
        response = self.session.get(url)
        return response.text.encode('utf-8')

    def post(self, url, data=''):
        response = self.session.post(url, data=data)
        return response.text.encode('utf-8')

    def encode_response(self, response):
        """解析订单操作返回的XML"""
        tree = ET.ElementTree(ET.fromstring(response))
        # print response
        if tree.find('Ack').text == 'Error':
            return False
        else:
            return True

    def process_order(self, order_id):
        """Process order"""
        url = self.api_url + 'format=xml&method=updateOrder'
        xml_data = '<UpdateOrderRequest><OrderId>{}</OrderId><Action>Process</Action></UpdateOrderRequest>'.format(
            order_id)
        response = self.post(url, xml_data)
        return self.encode_response(response)

    def charge_order(self, order_id):
        """Charge Order"""
        url = self.api_url + 'format=xml&method=updateOrder'
        xml_data = '<UpdateOrderRequest><OrderId>{}</OrderId><Action>Charge</Action></UpdateOrderRequest>'.format(
            order_id)
        response = self.post(url, xml_data)
        return self.encode_response(response)

    def cancle_order(self, order_id):
        """Cancle Order"""
        url = self.api_url + 'format=xml&method=updateOrder'
        xml_data = '<UpdateOrderRequest><OrderId>{}</OrderId><Action>Cancle</Action><CancelCode>1</CancelCode></UpdateOrderRequest>'.format(
            order_id)
        response = self.post(url, xml_data)
        return self.encode_response(response)

    def ship_order(self, order_id, shipping_method, tracking_number):
        """Ship Order"""
        url = self.api_url + 'format=xml&method=updateOrder'
        xml_data = '<UpdateOrderRequest><OrderId>{}</OrderId><Action>Ship</Action><ShippingMethod>{}</ShippingMethod><TrackingNumber>{}</TrackingNumber></UpdateOrderRequest>'.format(
            order_id, shipping_method, tracking_number)
        response = self.post(url, xml_data)
        return self.encode_response(response)

    def get_listings(self, Start=0, Status='Active', NumberOfItems='100', Format='json'):
        """Get Listings"""
        url = self.api_url + 'format=%s&method=getListings&Status=%s&NumberOfItems=%s&Start=%s' % (
            Format, Status, NumberOfItems, Start)
        body = self.get(url)
        try:
            return json.loads(body)
        except ValueError:
            return body

    def get_orders(self, from_date=None, to_date=None, status='New', start=0, limit=1000, format='xml'):
        """Get Orders"""
        url = self.api_url + 'format=%s&method=getOrders&Status=%s&Start=%d&NumberOfItems=%d' % (
            format, status, start, limit)
        if from_date:
            url += '&From=%s' % from_date
        if to_date:
            url += '&To=%s' % to_date

        body = self.get(url)
        return body

    def update_inventory(self, sku, qty):
        """Update Inventory"""
        url = self.api_url + 'format=xml&method=updateInventory'
        xml_data = '<UpdateInventoryRequest><SKU>{}</SKU><Action>update</Action><Quantity>{}</Quantity></UpdateInventoryRequest>'.format(
            sku, qty)
        response = self.post(url, xml_data)
        return self.encode_response(response)

    def get_payments(self, from_date, to_date, start=0, limit=100):
        """Get Payments"""
        url = self.api_url + 'format=json&method=getPayments&From={from_date}&To={to_date}&Start={start}&NumberOfItems={limit}'.format(
            from_date=from_date, to_date=to_date, start=start, limit=limit)
        response = self.get(url)
        json_data = json.loads(response)
        if 'Payments' in json_data.keys():
            return json_data['Payments']
        else:
            return list()

    def get_transactions(self, payment_id):
        """Get Transactions"""
        url = self.api_url + 'format=json&method=getTransactions&PaymentId=%s' % payment_id
        response = self.get(url)
        json_data = json.loads(response)
        return json_data['Payment']

