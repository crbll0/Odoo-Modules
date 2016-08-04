# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class ExtCjcRequest(models.Model):
    _inherit = 'cjc_request.cjc_request'

    tipo = fields.Selection((('cjc', 'caja chica'),
                             ('via', 'viaticos')), default='cjc')
    # viatico_registro_id = fields.Many2one('viatico.registro')

    # @api.multi
    # def registrar(self):
    #     view_id = self.env['ir.model.data'].get_object_reference(
    #         'cjc_request', 'cjc_request_wizard_view_form')[1]
    #
    #     if self.tipo == 'via':
    #         context = {
    #             'default_concept': self.viatico_registro_id.tipo.upper(),
    #             'default_reference_type': '01',
    #             'default_journal_id': 7,
    #             'default_line_ids': (0, 0, {
    #                 'concept_id': 19,
    #                 'amount': self.monto_solicitado})
    #         }
    #     else:
    #         context = self.env.context
    #
    #     wizard = {
    #         'name': 'Gasto Caja Chica',
    #         'view_mode': 'form',
    #         'view_id': False,
    #         'views': [(view_id, 'form')],
    #         'view_type': 'form',
    #         'res_model': 'cjc_request.wizard',
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #         'context': context,
    #     }
    #     return wizard

