# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleOrder(models.Model):
    """Sale Order"""

    _inherit = 'sale.order'

    walmart_id = fields.Many2one('walmart.el', string='Walmart Store')
    client_order_ref = fields.Char(required=True, copy=True)

    walmart_order_status = fields.Selection([
        ('Ordered', 'Ordered'),
        ('Shipped', 'Shipped'),
        ('Acknowledged', 'Acknowledged'),
        ('Cancelled', 'Cancelled')
    ], string='Walmart Order Status')



