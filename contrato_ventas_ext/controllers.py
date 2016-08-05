# -*- coding: utf-8 -*-
from openerp import http

# class ContratoVentasExt(http.Controller):
#     @http.route('/contrato_ventas_ext/contrato_ventas_ext/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contrato_ventas_ext/contrato_ventas_ext/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('contrato_ventas_ext.listing', {
#             'root': '/contrato_ventas_ext/contrato_ventas_ext',
#             'objects': http.request.env['contrato_ventas_ext.contrato_ventas_ext'].search([]),
#         })

#     @http.route('/contrato_ventas_ext/contrato_ventas_ext/objects/<model("contrato_ventas_ext.contrato_ventas_ext"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contrato_ventas_ext.object', {
#             'object': obj
#         })