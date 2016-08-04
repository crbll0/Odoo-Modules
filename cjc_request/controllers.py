# -*- coding: utf-8 -*-
from openerp import http

# class CjcRequest(http.Controller):
#     @http.route('/cjc_request/cjc_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cjc_request/cjc_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cjc_request.listing', {
#             'root': '/cjc_request/cjc_request',
#             'objects': http.request.env['cjc_request.cjc_request'].search([]),
#         })

#     @http.route('/cjc_request/cjc_request/objects/<model("cjc_request.cjc_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cjc_request.object', {
#             'object': obj
#         })