from odoo import http
from odoo.http import request


class Houzz(http.Controller):
    @http.route('/helloworld', auth='public')
    def hello_world(self):
        return request.render('houzz_el.hello')