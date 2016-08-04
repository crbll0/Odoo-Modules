# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployeeExt(models.Model):
    _inherit = 'hr.employee'

    @api.one
    def _count_acciones(self):
        for i in self:

            acciones = self.env['hr.personnel.action'].search(
                [('employee_id', '=', i.id)])

            self.num_acciones = len(acciones)

    @api.multi
    def open_accion_personal(self):
        window = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.personnel.action',
            'view_mode': 'tree,form',
            'context': {'default_employee_id': self.id},
            'domain': [('employee_id', '=', self.id)],
        }

        return  window

    num_acciones = fields.Integer(string='Acciones', compute='_count_acciones')