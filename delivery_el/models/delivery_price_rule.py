# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class PriceRule(models.Model):
    """扩展运费价格公式"""
    _inherit = 'delivery.price.rule'

    @api.depends('variable', 'operator', 'max_value', 'list_base_price', 'list_price', 'variable_factor')
    def _get_name(self):
        for rule in self:
            name = 'if %s %s %s then' % (rule.variable, rule.operator, rule.max_value)
            if rule.list_base_price and not rule.list_price:
                name = '%s fixed price %s' % (name, rule.list_base_price)
            elif rule.list_price and not rule.list_base_price:
                name = '%s %s times %s' % (name, rule.list_price, rule.variable_factor)
            else:
                name = '%s fixed price %s and %s times %s Extra' % (
                    name, rule.list_base_price, rule.list_price, rule.variable_factor)
            name = '%s First weight: %.2fKG Added weight: %.2fKG Discount: %.2f Length: %s %.2fCM Perimeter: %s %.2fCM Surcharge: %.2f VMN: %.2f' % (
                name, rule.first_weight, rule.added_weight, rule.discount, rule.length_operator, rule.max_length,
                rule.perimeter_operator, rule.max_perimeter, rule.surcharge, rule.volumetric_weight_numerator)
            rule.name = name

    first_weight = fields.Float('First weight', required=True)
    added_weight = fields.Float('Added weight', required=True)
    discount = fields.Float('Discount', default=1)
    # 最小重量
    min_weight = fields.Float('Min Weight', default=0)

    length_operator = fields.Selection([('==', '='), ('<=', '<='), ('<', '<'), ('>=', '>='), ('>', '>')],
                                       'Length Operator', default="<=")
    # 最长边
    max_length = fields.Float('Max Length', default=270.00)
    perimeter_operator = fields.Selection([('==', '='), ('<=', '<='), ('<', '<'), ('>=', '>='), ('>', '>')],
                                          'Perimeter Operator', default="<=")
    # 最大周长
    max_perimeter = fields.Float('Max Perimeter', default=327.00)
    surcharge = fields.Float('Fule Surcharge')
    # check_vw = fields.Boolean('Check volumetric weight')
    volumetric_weight_numerator = fields.Integer('Volumetric weight numerator', default=5000)
