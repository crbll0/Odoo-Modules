# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class MailComposeByTags(models.TransientModel):
    _inherit = 'mail.compose.message'

    tag = fields.Many2one('res.partner.category', string='Tag')

    @api.onchange('tag')
    def _onchange_tags(self):
        if self.tag:
            partners = self.env['res.partner'].search([
                ('category_id', '=', self.tag.id)])

            self.partner_ids += partners

