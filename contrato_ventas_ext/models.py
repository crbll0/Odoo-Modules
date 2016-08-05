# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class ContratosVentas(models.Model):
    _inherit = 'account.analytic.account'

    tipo = fields.Selection((('client', 'Cliente'), ('provider', 'Proveedo0r')), 'Tipo', default='client')

    @api.model
    def _prepare_invoice_data(self, contract):
        invoice_data = super(ContratosVentas, self)._prepare_invoice_data(contract)

        if contract.tipo == 'provider':
            account_id = self.env['res.partner'].browse(invoice_data['partner_id']).property_account_payable.id
            invoice_data.update({'type': 'in_invoice', 'account_id': account_id})

        return invoice_data

    @api.v7
    def _prepare_invoice_lines(self, cr, uid, contract, fiscal_position_id, context=None):
        fpos_obj = self.pool.get('account.fiscal.position')
        fiscal_position = None
        if fiscal_position_id:
            fiscal_position = fpos_obj.browse(cr, uid,  fiscal_position_id, context=context)
        invoice_lines = []
        for line in contract.recurring_invoice_line_ids:

            if contract.tipo == 'provider':
                res = line.product_id
                account_id = res.property_account_expense.id
                if not account_id:
                    account_id = res.categ_id.property_account_expense_categ.id
            else:
                res = line.product_id
                account_id = res.property_account_income.id
                if not account_id:
                    account_id = res.categ_id.property_account_income_categ.id

            account_id = fpos_obj.map_account(cr, uid, fiscal_position, account_id)

            taxes = res.taxes_id or False
            tax_id = fpos_obj.map_tax(cr, uid, fiscal_position, taxes)

            invoice_lines.append((0, 0, {
                'name': line.name,
                'account_id': account_id,
                'account_analytic_id': contract.id,
                'price_unit': line.price_unit or 0.0,
                'quantity': line.quantity,
                'uos_id': line.uom_id.id or False,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, tax_id)],
            }))
        return invoice_lines

#
# class ContratosVentasLineasFactura(models.Model):
#     _inherit = 'account.analytic.invoice.line'
#
#     account_id = fields.Many2one('account.account')