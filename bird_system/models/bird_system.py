# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from bdsys_api import BdsysApi

from odoo import api, fields, models
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class BirdSystem(models.Model):
    _name = 'bird.system'
    _rec_name = 'rma'

    rma = fields.Char('RMA')
    payment_reference = fields.Char(string='Order Id', required=True)
    contact = fields.Char('Contact', required=True)
    country_iso = fields.Many2one('res.country', string='Country', required=True)
    consignment_id = fields.Char('Consignment id')
    product_list = fields.One2many('bird.rma.product.list', 'rma_id', string='Product List', required=True)
    status = fields.Selection([
        ('PREPARING', 'PREPARING'),
        ('RECEIVED', 'RECEIVED'),
        ('PENDING', 'PENDING'),
        ('PROCESSING', 'PROCESSING'),
        ('FINISHED', 'FINISHED'),
        ('PROBLEM', 'PROBLEM'),
        ('CANCELLED', 'CANCELLED'),
        ('REVIEWING', 'REVIEWING'),
        ('DELETED', 'DELETED')
    ])

    @api.model
    def create(self, vals):
        bdsys_config = self.env['bird.system.config.settings'].browse(1)
        bdsys = BdsysApi(bdsys_config.bird_system_api_key, bdsys_config.bird_system_company_id)
        country = self.env['res.country'].browse(vals['country_iso'])
        response = bdsys.get_rma(payment_reference=vals['payment_reference'], contact=vals['contact'],
                                 country_iso=country.code)

        if response['success']:
            vals['rma'] = response['data']['sales_reference']
            vals['consignment_id'] = response['data']['id']
            # 添加产品
            for product in vals['product_list']:
                bd_product = self.env['bird.product'].browse(product[2]['product'])
                product_id = bd_product.product_id
                qty = product[2]['qty']
                add_product = bdsys.add_product(consignment_id=response['data']['id'], product_id=product_id,
                                                quantity=qty)
                _logger.info(add_product)

        return super(BirdSystem, self).create(vals=vals)

    @api.multi
    def unlink(self):
        """禁止删除"""
        return True

    @api.multi
    def update_status(self):
        """Update Status"""
        bdsys_config = self.env['bird.system.config.settings'].browse(1)
        bdsys = BdsysApi(bdsys_config.bird_system_api_key, bdsys_config.bird_system_company_id)
        for rma in self:
            rma_info = bdsys.get_rma_info(rma.consignment_id)
            if rma_info['success']:
                rma.update({
                    'status': rma_info['data'][0]['status']
                })
            else:
                raise ValidationError(rma_info['message'])
        return True


class BirdRmaProductList(models.Model):
    """RMA 产品列表"""
    _name = 'bird.rma.product.list'
    _description = 'RMA Product List'

    product = fields.Many2one('bird.product')
    qty = fields.Integer(default=1)
    rma_id = fields.Many2one('bird.system')


class BirdProduct(models.Model):
    """飞鸟产品对接"""
    _name = 'bird.product'
    _description = 'Bird System Product'
    _rec_name = 'sku'

    name = fields.Char(string='Name', required=True)
    name_customs = fields.Char(string='Name Customs', required=True)
    sku = fields.Char(string='SKU', required=True)
    product_id = fields.Char(string='Product Id')
    material = fields.Char('material', required=True)
    usage = fields.Char('usage', default='lighting', required=True)
    price_customs_export = fields.Float(string='Price Customs', default=20.00, required=True)
    customs_category_id = fields.Char('Customs Category Id', default='1043')
    customs_category_code = fields.Char(string='Customs Category', default='GB8539319100', required=True)
    brand = fields.Char('Brand', default='Null', required=True)
    weight = fields.Float(required=True)

    @api.model
    def get_product(self, start=0, limit=200):
        """拉取产品"""
        bdsys_config = self.env['bird.system.config.settings'].browse(1)
        bdsys = BdsysApi(bdsys_config.bird_system_api_key, bdsys_config.bird_system_company_id)
        products = bdsys.get_product(start=start, limit=limit)
        totals = products['total']
        # 保存数据
        for data in products['data']:
            product = self.search([('sku', '=', data['client_ref'])])
            if len(product) == 0:
                product_info = bdsys.get_product_info(data['id'])
                self.create({
                    'name': data['name'],
                    'name_customs': data['name_customs'],
                    'sku': data['client_ref'],
                    'product_id': data['id'],
                    'material': product_info['data'][0]['material'],
                    'usage': product_info['data'][0]['usage'],
                    'price_customs_export': data['price_customs_export'],
                    'customs_category_code': data['customs_category_code'],
                    'brand': data['brand']
                })
            else:
                product_info = bdsys.get_product_info(data['id'])
                for r in product:
                    # print product_info['data'][0]
                    r.update({
                        'material': product_info['data'][0]['material'],
                        'usage': product_info['data'][0]['usage']
                    })

        if totals > (start + limit):
            self.get_product(start + limit)
        else:
            return True

    @api.multi
    def put_product(self):
        """上传产品"""
        bdsys_config = self.env['bird.system.config.settings'].browse(1)
        bdsys = BdsysApi(bdsys_config.bird_system_api_key, bdsys_config.bird_system_company_id)
        for product in self:
            body = {
                'id': product.product_id,
                'name': product.name,
                'name_customs': product.name_customs,
                'material': product.material,
                'usage': product.usage,
                'brand': 'PU',
                'client_ref': product.sku,
                'customs_category_id': 1043,
                'customs_category_code': 'GB8539319100',
                'price_customs_export': product.price_customs_export,
                'status': 'PREPARING',
                'weight': product.weight,
                'product_product_customs_property[]': 0
            }
            add = bdsys.create_product(body)
            _logger.info(add)
            if add['success']:
                product.update({
                    'product_id': add['data']['id']
                })
            else:
                raise ValidationError(add['message'])

        return True



