# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class RefundEl(models.Model):
    """Order Refund"""

    _name = 'refund.el'
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order', string='Order')
    reason = fields.Selection([
        ('Quality issues', 'Quality issues'),
        ('Order is late', 'Order is late'),
        ('Customer returns', 'Customer returns'),
        ('Logistics damage', 'Logistics damage'),
        ('Customer canceled', 'Customer canceled'),
        ('Production problems', 'Production problems'),
        ('Logistics delays', 'Logistics delays'),
        ('Other', 'Other')
    ])
    currency_id = fields.Many2one('res.currency', string='Currency')
    refund_total = fields.Monetary(string='Refund Total', currency_field='currency_id')
    remark = fields.Text(string='Remarks')


class SaleOrder(models.Model):
    """Sale Order"""
    _inherit = 'sale.order'

    refund_el = fields.Float('Refund', compute='_compute_refund')

    @api.multi
    def _compute_refund(self):
        """计算退款金额"""
        for sale in self:
            refund = self.env['refund.el'].search([('order_id', '=', self.id)])
            sale.refund_el = 0.00
            for r in refund:
                sale.refund_el += r.refund_total

    @api.multi
    def action_refund_el(self):
        """
        This is refund order
        :return:
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('refund.el', 'view_refund_el')[0]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'sale.order',
            'default_order_id': self.ids[0],
            'default_refund_total': self.amount_total,
            'default_currency_id': self.pricelist_id.currency_id.id
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refund.el',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }




