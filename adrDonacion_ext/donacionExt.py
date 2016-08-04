# -*- coding: utf-8 -*-

import logging
from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)


class DonacionExt(osv.osv):

    _inherit = 'donation.campaign'

    def create(self, cr, uid, ids, context=None):
        seq = self.pool.get('ir.sequence').get(cr, uid, 'donation.campaign')

        ids['code'] = seq

        return super(DonacionExt, self).create(cr, uid, ids, context)

DonacionExt()
