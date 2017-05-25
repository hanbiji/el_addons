#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json


class BdsysApi(object):
    """海外仓，飞鸟API
    @demo: bdsys = BirdSystem('***********', '10')
           print bdsys.get_rma(contact='Test002', payment_reference='AMZ-112-5539603-3130663')
    """

    def __init__(self, api_key, company_id):
        self.session = requests.Session()
        self.session.headers['api_key'] = api_key
        self.session.headers['company_id'] = company_id

    def get_rma(self, contact, payment_reference=None, country_iso='US'):
        """client_id:
        id:
        return_consignment_action-id:32
        delivery_service_id:
        sales_reference:
        payment_reference:654321
        delivery_reference:
        update_time:2017-05-23 14:02:36
        contact:Test
        business_name:
        address_line1:
        address_line2:
        address_line3:
        city:
        county:
        post_code:
        country_iso:US
        telephone:
        email:
        special_instruction:
        neighbour_instruction:
        type:RETURN
        """
        url = 'http://www.birdsystem.com/client/Consignment/'
        body = {
            'return_consignment_action-id': 32,
            'payment_reference': payment_reference,
            'contact': contact,
            'country_iso': country_iso,
            'type': 'RETURN'
        }
        response = self.session.post(url, data=body)
        # r = json.load(response.text)
        return json.loads(response.text)

    def add_product(self, consignment_id, product_id, quantity):
        """
        id:
        consignment_id:1705230170037418
        product_id:238721
        quantity:1
        is_directional_shared_product:0
        :return: 
        """
        url = 'http://www.birdsystem.com/client/Consignment-Product/'
        body = {
            'consignment_id': consignment_id,
            'product_id': product_id,
            'quantity': quantity
        }
        response = self.session.post(url, data=body)
        return json.loads(response.text)

    def get_product(self, start=0, limit=200):
        """拉取所有产品"""
        url = 'http://www.birdsystem.com/client/Product/?start=%s&limit=%s' % (start, limit)
        response = self.session.get(url)
        return json.loads(response.text)








