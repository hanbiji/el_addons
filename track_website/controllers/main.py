# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class Track(http.Controller):

    @http.route('/track', auth='user', website=True)
    def index(self, **kwargs):
        TrackRefer = request.env['tracking.reference']
        tracks = TrackRefer.search([])
        return request.render('track_website.index', {'tracks': tracks})

    @http.route('/track/<model("tracking.reference"):track>', auth='user', website=True)
    def detail(self, track, **kwargs):
        return request.render('track_website.detail', {'track': track})

    @http.route('/track/add', website=True)
    def add(self, **kwargs):
        stock_pickings = request.env['stock.picking'].search([])
        carriers = request.env['delivery.carrier'].search([])
        return request.render('track_website.add', {'stock_pickings': stock_pickings, 'carriers': carriers})


    @http.route('/helloworld', auth='public')
    def hello_world(self):
        return('<h1>Hello World!</h1>')

    @http.route('/hello', website=True)
    def hello(self, **kwargs):
        return request.render('track_website.hello')

