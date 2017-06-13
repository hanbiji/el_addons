# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
import math

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    carrier_code = fields.Char('AMAZON Carrier Code')
    walmart_carrier_code = fields.Char('WALMART Carrier Code')
    houzz_carrier_code = fields.Char('HOUZZ Carrier Code')
    four_px = fields.Many2one('four.px', string='4PX')
    
    @api.multi
    def get_price_available(self, order):
        self.ensure_one()
        ship_price = total = weight = volume = quantity = length = width = height = 0
        total_delivery = 0.0
        order_items = []
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            length = line.product_id.length
            width = line.product_id.width
            height = line.product_id.height
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight = (line.product_id.weight or 0.0) * 1
            volume = (line.product_id.volume or 0.0) * 1
            quantity = qty
            ship_price += self.get_price_from_picking(total, weight, volume, quantity, length, width, height) * qty
            
        total = (order.amount_total or 0.0) - total_delivery

        total = order.currency_id.with_context(date=order.date_order).compute(total, order.company_id.currency_id)
        return ship_price

        #return self.get_price_from_picking(total, weight, volume, quantity, order)

    def get_price_from_picking(self, total, weight, volume, quantity, length, width, height):
        price = volumetric_weight = 0.0
        criteria_found = False
        price_dict = {'price': total, 'volume': volume, 'weight': weight, 'wv': volume * weight, 'quantity': quantity}
        
        for line in self.price_rule_ids:
            #算体积重
            if line.volumetric_weight_numerator>0:
                volumetric_weight = self.get_volumetric_weight(length, width, height, line.volumetric_weight_numerator)
                price_dict['weight'] = volumetric_weight if volumetric_weight > price_dict['weight'] else price_dict['weight']
                
            test = safe_eval(line.variable + line.operator + str(line.max_value), price_dict)
            
            #判断长是否超标
            test_l = True
            if line.max_length:
                l_dict = {'length':length}
                test_l = safe_eval('length' + line.length_operator + str(line.max_length), l_dict)
            #判断周长是否超标
            test_p = True
            if line.max_perimeter:
                perimeter = self.get_perimeter(length, width, height)
                p_dict = {'perimeter':perimeter}
                test_p = safe_eval('perimeter' + line.perimeter_operator + str(line.max_perimeter), p_dict)
                
            if test and test_l and test_p :
                if line.added_weight:
                    price = (line.list_base_price + line.list_price * math.ceil((price_dict[line.variable_factor]-line.first_weight)/line.added_weight)) * line.discount
                else:
                    price = (line.list_base_price + line.list_price * price_dict[line.variable_factor]) * line.discount
                
                criteria_found = True
                break
            
        if not criteria_found:
            raise UserError(_("Selected product in the delivery method doesn't fulfill any of the delivery carrier(s) criteria."))
 
        return price
    
    def get_perimeter(self, length, width, height):
        '计算周长，周长公式：l+w*2+h*2'
        return length + width*2 + height*2
    
    def get_volumetric_weight(self, length, width, height, volumetric_weight_numerator):
        '计算体积重'
        return (length * width * height)/volumetric_weight_numerator


