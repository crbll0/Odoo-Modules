# -*- coding: utf-8 -*-

import pdb

from openerp import models, fields, api
from openerp.exceptions import Warning


class BankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')

    @api.multi
    def process_reconciliation(self, mv_line_dicts):
        if self.ref:
            invoice_line = self.env['account.invoice'].search([('number', '=', self.ref)]).invoice_line
            if invoice_line:
                self.account_analytic_id = invoice_line[0].account_analytic_id

        self = self.with_context(from_parent_object=True)
        return super(BankStatementLine, self).process_reconciliation(mv_line_dicts)
