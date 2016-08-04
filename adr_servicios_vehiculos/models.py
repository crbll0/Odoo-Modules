# -*- coding: utf-8 -*-
import datetime
import logging
import pdb
from openerp import api, fields, models
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)


class ServicioVehiculo(models.Model):
    _name = 'fleet.transport.services'

    def _get_solic_id(self):
        return self.env.uid

    def _datetime_now(self):
        return datetime.datetime.now()

    def vehiculos_disponibles(self):
        # vehiculos_obj = self.env['fleet.vehicle']
        solicitudes = self.search([('state', '=', 'asig')])

        vehiculos_ocupados = []
        for solicitud in solicitudes:
            vehiculos_ocupados.append(solicitud.vehiculo_id.id)

        # vehiculos = vehiculos_obj.search([('id', 'not in', vehiculos_ocupados)])

        return [('id', 'not in', vehiculos_ocupados)]
        # return [('id', 'in', [str(id) for id in vehiculos_ocupados])]


    secuencia = fields.Char(string='Secuencia', readonly=True)
    solicitante_id = fields.Many2one('res.users', string='Solicitante',
                                     default=_get_solic_id, readonly=True)
    department_id = fields.Many2one('hr.department', string='Departamento', readonly=True)
    fecha_solicitud = fields.Datetime(string='Fecha Solicitud', default=_datetime_now, readonly=True)
    fecha_desde = fields.Datetime(string='Fecha Desde', required=True)
    fecha_hasta = fields.Datetime(string='Fecha Hasta', required=True)
    destino_id = fields.Many2one('viatico.zonas', string='Destino', required=True)
    vehiculo_id = fields.Many2one('fleet.vehicle', string='Vehiculo', domain=vehiculos_disponibles)
    notas = fields.Text(string='Notas', required=True)

    state = fields.Selection((('solic', 'Solicitado'),
                             ('confirm','Confirmado'),
                             ('asig','Trans. Asignado'),
                             ('done','Completado'),
                             ('cancel', 'Cancelado')),
                            string='Estado', default='solic')

    stage = fields.Selection((('solic', 'Esperando Confirmacion'),
                             ('confirm', 'Esperando Asignacion de Transp.'),
                             ('asig', 'En Servicio'),
                             ('done', 'Completado')),
                            string='Etapa', default='solic')

    solicitado_por = fields.Many2one('res.users', string='Solicitado', readonly=True)
    confirmacion_por = fields.Many2one('res.users', string='Confirmacion', readonly=True)
    asignacion_por = fields.Many2one('res.users', string='Asig. Transp.', readonly=True)
    compleatdo_por = fields.Many2one('res.users', string='Completado', readonly=True)
    cancelado_por = fields.Many2one('res.users', string='Cancelado', readonly=True)

    origen = fields.Char(string='Origen')
    # ocupado = fields.Boolean()

    @api.onchange('solicitante_id')
    def _onchenge_solicitante(self):
        depart = self.env['hr.employee'].search(
            [('user_id', '=', self.solicitante_id.id)]).department_id.id

        self.department_id = depart

    @api.onchange('vehiculo_id')
    def onchange_vehiculo(self):
        # vehiculos_obj = self.env['fleet.vehicle']
        solicitudes = self.search([('state', '=', 'asig')])

        vehiculos_ocupados = []
        for solicitud in solicitudes:
            vehiculos_ocupados.append(solicitud.vehiculo_id.id)

        if self.vehiculo_id.id in vehiculos_ocupados:
            self.vehiculo_id = ''
            return {'domain': {
                'vehiculo_id': [('id', 'not in', vehiculos_ocupados)]}}


    @api.one
    def confirmacion(self):
        self.write({'state': 'confirm', 'stage': 'confirm',
                    'confirmacion_por': self.env.uid})

    @api.one
    def asignacion_transporte(self):
        self.write({'state': 'asig', 'stage': 'asig',
                    'asignacion_por': self.env.uid})

    @api.one
    def completado(self):
        self.write({'state': 'done', 'stage': 'done',
                    'compleatdo_por': self.env.uid})

    @api.one
    def cancelar(self):
        self.write({'state': 'cancel', 'cancelado_por': self.env.uid})

    @api.model
    def create(self, values):
        values['secuencia'] = self.env['ir.sequence'].get('fleet.transport.services')
        values['solicitado_por'] = self.env.uid
        values['department_id'] = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)]).department_id.id

        return super(ServicioVehiculo, self).create(values)