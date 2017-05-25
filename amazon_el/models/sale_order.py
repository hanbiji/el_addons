# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleOrder(models.Model):
    """Sale Order"""

    _inherit = 'sale.order'

    amazon_id = fields.Many2one('amazon', string='Amazon Store')
    fulfillment_channel = fields.Selection([('MFN', 'MFN'), ('AFN', 'AFN')], string='Fulfillment Channel')
    client_order_ref = fields.Char(required=True)
    amazon_order_status = fields.Selection([
        ('PendingAvailability', 'PendingAvailability'),
        ('Pending', 'Pending'),
        ('Unshipped', 'Unshipped'),
        ('PartiallyShipped', 'PartiallyShipped'),
        ('Shipped', 'Shipped'),
        ('Canceled', 'Canceled'),
        ('Unfulfillable', 'Unfulfillable')
    ])


class SaleOrderLine(models.Model):
    """sale.order.line"""
    _inherit = 'sale.order.line'

    amazon_order_item_id = fields.Char('Order Item Id')





