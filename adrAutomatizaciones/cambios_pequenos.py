# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class MakeDeposit(models.Model):
    _inherit = 'deposit.ticket'

    secuencia = fields.Char(string='Secuencia', readonly=True)

    @api.model
    def create(self, values):
        vals = super(MakeDeposit, self).create(values)

        vals['secuencia'] = self.env['ir.sequence'].get('deposit.ticket')

        return vals


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    def proforma_voucher(self):
        res = super(AccountVoucher, self).proforma_voucher()

        invoice_obj = self.env['account.invoice']

        for move in self:
            for line in move.line_cr_ids:

                inv = line.move_line_id.invoice
                number = line.move_line_id.move_id.name

                if inv:
                    factura = invoice_obj.search([
                        ('id', '=', inv.id)]).related_invoice_id
                else:
                    factura = invoice_obj.search([
                        ('name', '=', number)]).related_invoice_id
                if factura:
                    # total = factura.amount_total
                    saldo = factura.residual
                    # saldo_temp = total if not saldo else saldo

                    saldo -= line.amount
                    factura.residual = saldo

                    if saldo == 0:
                        factura.state = 'paid'

        return res
