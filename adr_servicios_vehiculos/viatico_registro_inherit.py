# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class ViaticoRegistronInherit(models.Model):
    _inherit = 'viatico.registro'

    def vehiculos_disponibles(self):
        # vehiculos_obj = self.env['fleet.vehicle']
        solicitudes = self.env['fleet.transport.services'].search(
            [('state', '=', 'asig')])

        vehiculos_ocupados = []
        for solicitud in solicitudes:
            vehiculos_ocupados.append(solicitud.vehiculo_id.id)

        # vehiculos = vehiculos_obj.search([('id', 'not in', vehiculos_ocupados)])

        return [('id', 'not in', vehiculos_ocupados)]
        # return [('id', 'not in', [str(id) for id in vehiculos_ocupados])]

    vehiculo = fields.Many2one('fleet.vehicle', string='Vehiculo', domain=vehiculos_disponibles)

    @api.onchange('vehiculo')
    def onchange_vehiculo(self):
        # vehiculos_obj = self.env['fleet.vehicle']
        solicitudes = self.env['fleet.transport.services'].search(
            [('state', '=', 'asig')])

        vehiculos_ocupados = []
        for solicitud in solicitudes:
            vehiculos_ocupados.append(solicitud.vehiculo_id.id)

        if self.vehiculo.id in vehiculos_ocupados:
            self.vehiculo_id = ''
            return {'domain': {
                'vehiculo_id': [('id', 'not in', vehiculos_ocupados)]}}


    @api.multi
    def validar(self):
        res = super(ViaticoRegistronInherit, self).validar()

        solicitante = self.solicitante.id
        depart = self.departamento.id

        solic = self.solicitado_por.id
        confirm = self.confirmado_por.id
        asig = self.tranps_por.id

        vehiculo = self.vehiculo.id
        zona = self.zonas_id.id

        f_solic = self.fecha_solicitud
        f_desde = self.fecha_viaje_desde
        f_hasta = self.fecha_viaje_hasta

        self.env['fleet.transport.services'].create({
            'solicitante_id': solicitante,
            'department_id': depart,
            'fecha_solicitud': f_solic,
            'fecha_desde': f_desde,
            'fecha_hasta': f_hasta,
            'destino_id': zona,
            'vehiculo_id': vehiculo,
            'solicitado_por': solic,
            'confirmacion_por': confirm,
            'asignacion_por': asig,
            'origen': self.secuencia,
            'state': 'asig',
            'stage': 'asig'
        })

        return res