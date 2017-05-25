#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pycurl
import certifi
import json
from StringIO import StringIO
from urllib import urlencode
from json.encoder import JSONEncoder
from pyasn1.compat.octets import null
from dircache import cache
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class  HouzzApi(object):
    'Houzz api'
    def __init__(self, token, user_name, app_name):
        self.token = token
        self.user_name = user_name
        self.app_name = app_name
        self.api_url = 'https://api.houzz.com/api?'

    def get(self, url):
        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(c.CAINFO, certifi.where())
        c.setopt(c.URL, url)

        header = [
            'X-HOUZZ-API-SSL-TOKEN: ' + self.token,
            'X-HOUZZ-API-USER-NAME: ' + self.user_name,
            'X-HOUZZ-API-APP-NAME: ' + self.app_name
            ]
        c.setopt(c.HTTPHEADER, header)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        return buffer.getvalue()

    def post(self, url, data=''):
        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(c.CAINFO, certifi.where())
        c.setopt(c.URL, url)

        header = [
            'X-HOUZZ-API-SSL-TOKEN: ' + self.token,
            'X-HOUZZ-API-USER-NAME: ' + self.user_name,
            'X-HOUZZ-API-APP-NAME: ' + self.app_name,
            "Content-type: text/xml"
            ]
        c.setopt(c.HTTPHEADER, header)
        c.setopt(c.CUSTOMREQUEST, 'POST')
        c.setopt(c.POSTFIELDS, data)

        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        return buffer.getvalue()

    def encode_response(self, response):
        """解析订单操作返回的XML"""
        tree = ET.ElementTree(ET.fromstring(response))
        if tree.find('Ack').text == 'Error':
            # print response
            return False
        else:
            return True

    def process_order(self, order_id):
        """Process order"""
        url = self.api_url + 'format=xml&method=updateOrder'
        xml_data = '<UpdateOrderRequest><OrderId>{}</OrderId><Action>Process</Action></UpdateOrderRequest>'.format(order_id)
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
        url = self.api_url + 'format=%s&method=getListings&Status=%s&NumberOfItems=%s&Start=%s' % (Format, Status, NumberOfItems, Start)
        body = self.get(url)
        try:
            return json.loads(body)
        except ValueError:
            return body

    def get_orders(self, from_date=None, to_date=None, status='New', start=0, limit=1000, Format='xml'):
        """Get Orders"""
        url = self.api_url + 'format=%s&method=getOrders&Status=%s&Start=%d&NumberOfItems=%d' % (Format, status, start, limit)
        if from_date:
            url += '&From=%s' % from_date
        if to_date:
            url += '&To=%s' % to_date

        body = self.get(url)
        return body

    def update_inventory(self, sku, qty):
        """Update Inventory"""
        url = self.api_url + 'format=xml&method=updateInventory'
        xml_data = '<UpdateInventoryRequest><SKU>{}</SKU><Action>update</Action><Quantity>{}</Quantity></UpdateInventoryRequest>'.format(sku, qty)
        response = self.post(url, xml_data)
        return self.encode_response(response)


