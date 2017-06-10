# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.track_website.controllers.main import Track

class TrackExtended(Track):
    @http.route(['/hello', '/hello/<name>'])
    def hello(self, name=None, **kwargs):
        response = super(TrackExtended, self).hello()
        response.qcontext['name'] = name
        return response




