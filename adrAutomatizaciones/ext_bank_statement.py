# -*- coding: utf-8 -*-

import pdb

from openerp import models, fields, api
from openerp.exceptions import Warning


class BankStatement(models.Model):
    _inherit = 'account.bank.statement'

    balance_end = fields.Float(compute='recalc_end_balance', store=True)

    @api.one
    @api.depends('line_ids')
    def recalc_end_balance(self):
        balance_end = self.balance_start

        for line in self.line_ids:
            balance_end += line.amount

        self.balance_end = balance_end

    @api.one
    def actualizar_monto(self):

        balance_end = self.balance_start

        for line in self.line_ids:
            balance_end += line.amount

        self.balance_end = balance_end


