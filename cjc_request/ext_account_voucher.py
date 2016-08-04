# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class AccountVoucerLine(models.Model):
    _inherit = 'account.voucher'
    #
    # @api.one
    # def account_move_get(self):
    #     move = super(AccountVoucerLine, self).account_move_get()
    #
    #     move['account_analytic_id'] = self.


