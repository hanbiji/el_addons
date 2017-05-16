# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

import odoo.addons.decimal_precision as dp

class TrackingReference(models.Model):
    '订单物流跟踪编号'
    _name='tracking.reference'
    _description = "Tracking Reference"
    
    stock_picking_id = fields.Many2one('stock.picking', required=True)
    tracking_ref = fields.Char(string='Tracking Reference', copy=False, required=True)
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", required=True)
    weight = fields.Float('Weight')
    estimated_cost = fields.Float('Estimated cost')
    actual_cost = fields.Float('Actual cost')
    fuel_cost = fields.Float('Fuel cost')
    total_cost = fields.Float('Total cost')
    pay = fields.Boolean('Pay')
    pay_date = fields.Date('Pay date')
        
    
    _sql_constraints = [
        ('ref_uniq', 'unique(tracking_ref, carrier_id)', 'Reference must be unique per picking!'),
    ]
    
    @api.model
    def load(self, fields, data):
        'import'
        _logger.info(fields)
        _logger.info(data)
        not_id = False
        if 'id' not in fields:
            fields.insert(0, 'id')
            not_id = True
            
        for key,i in enumerate(data):
            _logger.info(i)
            track = self.search_read([('tracking_ref', '=', i[0])])
            if track:
                for tr in track:
                    if not_id:
                        data[key].insert(0, '__export__.tracking_reference_' + str(tr['id']))
                    
        _logger.info(fields)
        _logger.info(data)
        
        #import pdb; pdb.set_trace()
        result = super(TrackingReference, self).load(fields, data)
        if result['ids']:
            #其它操作
            pass
        return result
        #raise UserError(_("Selected product in the delivery method doesn't fulfill any of the delivery carrier(s) criteria."))
    
    
