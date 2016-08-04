# -*- coding: utf-8 -*-

import logging
from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)


# class FacturaClienteExt(osv.osv):
#
#     _inherit = 'account.invoice'
#
#     _columns = {
#         'cobertura': fields.integer('Cobertura', (16, 2)),
#         'name_analytic_account': fields.char('Cuenta Analitica'),
#     }
#     _defaults ={
#         'cobertura': 0.00,
#         'name_analytic_account': '',
#     }
#     '''
#     def invoice_validate(self, cr, uid, ids, context=None):
#         self.pool.get('account.invoice').button_reset_taxes(cr, uid, ids, context)
#
#         return super(FacturaClienteExt, self).invoice_validate(cr, uid, ids, context)
#     '''




# FacturaClienteExt()
