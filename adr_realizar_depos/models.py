# -*- coding: utf-8 -*-

from openerp import models, fields, api


class AdrRealizarDepos(models.Model):
    _inherit = 'deposit.ticket'

    state = fields.Selection(
        (
            ('draft', 'Borrador'),
            ('to_be_reviewed', 'Listo para Revision'),
            ('auditar', 'Auditado'),
            ('done', 'Realizado'),
            ('cancel', 'Cancelado'),
        ), string='Estado'
    )

    stage = fields.Selection(
        (
            ('draft', 'Esperando para ser Revisado'),
            ('to_be_reviewed', 'Esperando para Auditar'),
            ('auditar', 'Esperando para ser Procesado'),
            ('done', 'Realizado'),
        ), string='Etapa'
    )

    _defaults = {
        'stage': 'draft',
    }

    @api.one
    def action_review(self):
        self.stage = 'to_be_reviewed'
        return super(AdrRealizarDepos, self).action_review()

    @api.one
    def action_process(self):
        self.stage = 'done'
        return super(AdrRealizarDepos, self).action_process()

    @api.one
    def action_auditar(self):
        self.write({'state': 'auditar', 'stage': 'auditar'})
