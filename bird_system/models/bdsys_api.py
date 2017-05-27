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
        return json.loads(response.text.encode('utf-8'))

    def get_rma_info(self, consignment_id):
        """Get Rma By Id"""
        url = 'http://www.birdsystem.com/client/Consignment/?id=%s&type=RETURN' % consignment_id
        response = self.session.get(url)
        return json.loads(response.text.encode('utf-8'))

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
        return json.loads(response.text.encode('utf-8'))

    def get_product(self, start=0, limit=200):
        """拉取所有产品"""
        url = 'http://www.birdsystem.com/client/Product/?start=%s&limit=%s' % (start, limit)
        response = self.session.get(url)
        return json.loads(response.text.encode('utf-8'))

    def get_product_info(self, product_id):
        """获取产品详细信息"""
        url = 'http://www.birdsystem.com/client/Product/?id=%s' % product_id
        response = self.session.get(url)
        return json.loads(response.text.encode('utf-8'))

    def create_product(self, body):
        """添加产品
        http://www.birdsystem.com/client/Product/
        id:
        client_id:
        name:test
        name_customs:test
        material:test
        usage:test
        brand:test
        customs_category_id:591
        customs_category_code:GB8529905000
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        product_product_customs_property[]:0
        note:
        client_ref:
        commodity_code:
        company_product-is_shared_internal:0
        description:
        company_product-price:
        company_product-cost:
        price_customs_import:
        price_customs_export:20
        company_product-low_stock_level:
        inventory_time:
        status:PREPARING
        :return: 
        """
        url = 'http://www.birdsystem.com/client/Product/'
        response = self.session.post(url, data=body)
        return json.loads(response.text.encode('utf-8'))








