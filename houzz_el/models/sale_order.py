# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..models.houzzApi import *

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Sale Order"""
    _inherit = 'sale.order'

    houzz_config_id = fields.Many2one('houzz.config', string='Houzz')
    client_order_ref = fields.Char(required=True)
    houzz_order_status = fields.Selection([
        ('Placed', 'Placed'),
        ('Processing', 'Processing'),
        ('Charged', 'Charged'),
        ('FailedToCharge', 'Failed to Charge'),
        ('Shipped', 'Shipped'),
        ('Canceled', 'Canceled')
    ], string='Houzz Order Status')

    @api.multi
    # @api.onchange('houzz_order_status')
    def houzz_process_order(self):
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz_config_id.houzz_token, user_name=self.houzz_config_id.houzz_user_name, app_name=self.houzz_config_id.name)
        process = houzz.process_order(self.client_order_ref)

        if not process:
            self.message_post(body=u"确认订单失败")
            # raise UserError(u'确认订单失败')
        else:
            self.update({'houzz_order_status': 'Processing'})
            self.message_post(body=u"订单已确认")
            # raise UserError(u'订单已确认')
        return True
        # warning = {
        #     'title': 'Process',
        #     'message': 'OK',
        # }
        # return {'warning': warning}


    @api.multi
    # @api.onchange('state')
    def houzz_charge_order(self):
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz_config_id.houzz_token, user_name=self.houzz_config_id.houzz_user_name,
                         app_name=self.houzz_config_id.name)
        process = houzz.charge_order(self.client_order_ref)
        # _logger.info(process)

        if not process:
            self.message_post(body=u"收款失败")
            # raise UserError(u'确认订单失败')
        else:
            self.update({'houzz_order_status': 'Charged'})
            self.message_post(body=u"收款成功")
            # raise UserError(u'订单已确认')
        return True
        # warning = {
        #     'title': 'Process',
        #     'message': 'OK',
        # }
        # return {'warning': warning}






