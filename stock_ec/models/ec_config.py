# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# 易仓系统的配置

from odoo import models, fields, api

class EcConfig(models.Model):
    """易仓系统的配置"""
    _name = 'ec.config'
    _description = 'EC System Profile'
    _rec_name = 'ec_name'

    ec_name = fields.Char(string="Ec Stock Name")
    app_token = fields.Char(string="App Token")
    app_key = fields.Char(string="App Key")
    wsdl_server = fields.Char(string="WSDL Server")
