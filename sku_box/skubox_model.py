# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SkuBox(models.Model):
    _name = 'sku.box'
    _inherit = ['mail.thread']
    _description = 'Platform SKU comparison table'
    team_id = fields.Many2one('crm.team', 'Team', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    name = fields.Char('Title', required=True)
    sku = fields.Char('SKU', required=True)
    
    @api.constrains('sku', 'team_id')
    def _check_name_size(self):
        for skupost in self:
            check = self.env['sku.box'].search([('team_id', '=', skupost.team_id.id), ('sku', '=', skupost.sku)])
            if len(check)>1:
                raise ValidationError('Team SKU is have!' )

    
#     @api.model
#     def create(self, vals):
#         '''保证各平台SKU的唯一性'''
#         check = self.search([('team_id', '=', vals['team_id']), ('sku', '=', vals['sku'])])
#         if not check:
#             sku = super(SkuBox, self).create(vals)
#             return sku
#         else:
#             return check[0]