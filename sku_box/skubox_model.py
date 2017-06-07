# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SkuBox(models.Model):
    """Platform SKU"""
    _name = 'sku.box'
    _inherit = ['mail.thread']
    _description = 'Platform SKU comparison table'
    # _sql_constraints = [('sku_product_uniq'), 'UNIQUE(sku, product_id)', 'SKU Must Be Unique!']
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', required=True)
    sku = fields.Char('SKU', required=True)
    
    @api.constrains('sku', 'product_id')
    def _check_name_size(self):
        for skupost in self:
            check = self.env['sku.box'].search_count([('product_id', '=', skupost.product_id.id), ('sku', '=', skupost.sku)])
            if check > 1:
                raise ValidationError('%d Team SKU is have!' % check)




