# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class FleetInherit(models.Model):
    _inherit = 'fleet.vehicle'

    def _count_tranps(self):
        transp = self.env['fleet.transport.services'].search(
            [('vehiculo_id', '=', self.id)])

        self.count_transp = len(transp)

    @api.multi
    def open_transport_services(self):
        window = {
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.transport.services',
            'view_mode': 'tree,form',
            'context': {'default_vehiculo_id': self.id},
            'domain': [('vehiculo_id', '=', self.id)],
        }

        return  window

    count_transp = fields.Integer(string='Transporte', compute='_count_tranps')


