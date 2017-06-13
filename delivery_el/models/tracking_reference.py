# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class TrackingReference(models.Model):
    """订单物流跟踪编号"""
    _name = 'tracking.reference'
    _description = "Tracking Reference"
    _rec_name = 'tracking_ref'
    
    stock_picking_id = fields.Many2one('stock.picking', string=u"发货单", required=True)
    tracking_ref = fields.Char(string='Tracking Reference', copy=False, required=True)
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", required=True)
    weight = fields.Float('Weight')
    estimated_cost = fields.Float('Estimated Cost')
    actual_cost = fields.Float('Actual Cost')
    fuel_cost = fields.Float('Fuel Cost')
    total_cost = fields.Float('Total Cost')
    pay = fields.Boolean('Pay')
    pay_date = fields.Date('Pay Date')
    upload_store = fields.Boolean('Upload Store', default=False)
    _sql_constraints = [
        ('ref_uniq', 'unique(tracking_ref, carrier_id)', 'Reference must be unique per picking!'),
    ]
    
    @api.model
    def load(self, fields, data):

        """批量导入物流单号"""

        not_id = False
        if 'id' not in fields:
            # 表格中如果没有id列，自动增加
            fields.insert(0, 'id')
            not_id = True
            
        for key, i in enumerate(data):
            # 查询是否已存在物流单号，存在更新表格中的id，对原有数据进行更新
            track = self.search_read([('tracking_ref', '=', i[0])])
            if track:
                for tr in track:
                    if not_id:
                        data[key].insert(0, '__export__.tracking_reference_' + str(tr['id']))

        result = super(TrackingReference, self).load(fields, data)
        if result['ids']:
            # 其它操作
            pass
        return result

