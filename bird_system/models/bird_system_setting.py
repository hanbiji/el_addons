# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class BirdSystemSettings(models.Model):
    _name = 'bird.system.config.settings'
    _inherit = 'res.config.settings'

    bird_system_api_key = fields.Char('API KEY')
    bird_system_company_id = fields.Char('Company ID')

    @api.model
    def default_get(self, fields):
        res = super(BirdSystemSettings, self).default_get(fields)
        if 'id' in fields or not fields:
            r = self.browse(res['id'])
            res['bird_system_api_key'] = r.bird_system_api_key
            res['bird_system_company_id'] = r.bird_system_company_id
        return res





