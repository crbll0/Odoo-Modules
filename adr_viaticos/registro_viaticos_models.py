# -*- coding: utf-8 -*-

import datetime
import logging
import pdb

from openerp import api, fields, models
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)


class RegistroDeViaticos(models.Model):
    _name = 'viatico.registro'

    def _get_solic_id(self):
        return self.env.uid

    def _datetime_now(self):
        return datetime.datetime.now()

    def _get_department(self, solicitante_id):
        depart = self.env['hr.employee'].search(
            [('user_id', '=', solicitante_id)]).department_id.id

        return depart


    secuencia = fields.Char(string='Secuencia', readonly=True)

    solicitante = fields.Many2one('res.users', string='Solicitante',
                                  default=_get_solic_id, readonly=True)
    departamento = fields.Many2one('hr.department', readonly=True)

    fecha_solicitud = fields.Datetime(readonly=True, default=_datetime_now)
    fecha_viaje_desde = fields.Datetime(string='Desde')
    fecha_viaje_hasta = fields.Datetime(string='Hasta')

    tipo = fields.Selection((('viatico', 'Viatico'), ('dieta', 'Dieta')),
                            default='viatico', required=True)
    zonas_id = fields.Many2one('viatico.zonas', string='Zona', required=True)
    escala_id = fields.Many2one('viatico.escala', string='Escala',
                                required=True)

    vehiculo = fields.Many2one('fleet.vehicle', string='Vehiculo')
    # campo boolean informativo para saber si el veichulo esta o no registrado en una zona
    # para asi mostrar un mensaje de advertencia si el vehiculo no se encuentra
    vehiculo_en_zona = fields.Boolean(default=False)

    registro_lines = fields.One2many('viatico.registro.line', 'registro_id',
                                     required=True)

    total = fields.Float(compute='_onchange_lineas')

    state = fields.Selection((('solic', 'Solicitado'),
                              ('confirm', 'Confirmado'),
                              ('transp', 'Transporte Asignado'),
                              ('val', 'Validado'),
                              ('completado', 'Completado'),
                              ('cancel', 'Cancelado')),
                             default='solic', string='Estado')

    stage = fields.Selection((('solic', 'Esperando Confirmacion'),
                              (
                              'confirm', 'Esperando Asignacion de Transporte'),
                              ('transp', 'Esperando Validacion'),
                              ('val', 'Completado')),
                             default='solic', string='Etapa')

    notas = fields.Text(string='Notas')

    solicitado_por = fields.Many2one('res.users', string='Solicitado por',
                                     readonly=True)
    confirmado_por = fields.Many2one('res.users', string='Confirmado por',
                                     readonly=True)
    tranps_por = fields.Many2one('res.users', string='Asig. de Transporte por',
                                 readonly=True)
    validado_por = fields.Many2one('res.users', string='Valiado por',
                                   readonly=True)
    cancelado_por = fields.Many2one('res.users', string='Cancelado por',
                                    readonly=True)

    @api.onchange('registro_lines')
    def _onchange_lineas(self):
        total = 0
        for line in self.registro_lines:
            total += sum([line.desayuno, line.almuerzo, line.cena,
                         line.alojamiento, line.dia_completo, line.gasto_imp,
                          line.gasto_estra])

            self.total = total

    @api.onchange('escala_id')
    def _onchange_escala(self):
        zonas = self.env['viatico.zonas'].search([
            ('escala_id', '=', self.escala_id.id)])
        if zonas:
            value = [x.id for x in zonas]
            self.zonas_id = False
            return {'domain': {'zonas_id': [('id', 'in', value)]}}

    @api.onchange('solicitante')
    def _onchange_solicitante(self):
        depart = self.env['hr.employee'].search(
            [('user_id', '=', self.solicitante.id)]).department_id.id

        self.departamento = depart

    @api.onchange('vehiculo')
    def _onchange_vehiculo(self):
        esta = False
        for line in self.zonas_id.vehiculos_ids:
            if line.vehiculo_id.id == self.vehiculo.id:
                esta = True
        self.vehiculo_en_zona = esta

    @api.multi
    def confirm(self):
        self.write({'state': 'confirm', 'stage': 'confirm',
                    'confirmado_por': self.env.uid})

    @api.multi
    def validar(self):
        peaje = 0
        for line in self.zonas_id.vehiculos_ids:
            if line.vehiculo_id.id == self.vehiculo.id:
                peaje = line.peaje
        concepto = 'Documento Origen: %s\n\n' % self.secuencia
        concepto += "Fecha desde: %s \t hasta: %s \t\t\t\t Lugar: %s \t\t\t\t Tipo: %s\n\n" % (
            self.fecha_viaje_desde, self.fecha_viaje_hasta, self.zonas_id.name,
            self.tipo.upper())

        for line in self.registro_lines:
            concepto += '%s\n' % line.employee_id.name
            concepto += '\tDesayuno: RD$ %d | Almuerzo: RD$ %d | Cena: RD$ %d' % (
                line.desayuno, line.almuerzo, line.cena
            )
            if self.tipo == 'viatico':
                concepto += ' | Alojamiento: RD$ %d |Gasto Extra.: RD$ %d | Gasto Impuestos.: RD$ %d' % (
                    line.alojamiento, line.gasto_estra, line.gasto_imp)
            concepto += '\n'

        concepto += '\nPEAJE: RD$ %d\n\n' % peaje
        concepto += self.notas + '\n' if self.notas else ""


        cjc_obj = self.env['cjc_request.cjc_request']
        dep_id = self.env['hr.employee'].search(
            [('user_id', '=', self.solicitante.id)]).department_id.id

        cjc_id = cjc_obj.create({
            'usuario': self.solicitante.id,
            'solicitado_por': self.solicitante.id,
            'departamento': dep_id,
            'monto_solicitado': self.total + peaje,
            'concepto': concepto,
            'tipo': 'via',
            # 'viatico_registro_id': self.id,
        })
        cjc_id.write({'state': 'validar1', 'stage': 'validar1', 'validado1_por': self.confirmado_por.id})
        self.write(
            {'state': 'val', 'stage': 'val', 'validado_por': self.env.uid})
        return True

    @api.multi
    def cancel(self):
        self.write({'state': 'cancel', 'cancelado_por': self.env.uid})

    @api.multi
    def asignacion(self):
        self.write({'state': 'transp', 'stage': 'transp',
                    'tranps_por': self.env.uid})

    @api.model
    def create(self, values):
        values['departamento'] = self._get_department(self._get_solic_id())
        values['secuencia'] = self.env['ir.sequence'].get('viatico.registro')
        values['solicitado_por'] = self.env.uid

        return super(RegistroDeViaticos, self).create(values)


class RegistroDeViaticosLines(models.Model):
    _name = 'viatico.registro.line'

    def str_to_datetime(self, str_date):
        """
        Convierte fechas dadas en formato <string> a formato <datetime>.

        El parametro str_date puede ser una fecha o una lista de fechas.
        : param str_date: '2016/2/14' or ['2016/2/14', '2016/2/27']
        : return: datetime(2016, 2. 14) or [datetime(2016, 2, 14), ...]
        """

        if isinstance(str_date, list):
            fechas = []
            for date in str_date:
                fecha = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                fecha = datetime.date(fecha.year, fecha.month, fecha.day)
                fechas.append(fecha)

            return fechas

        elif isinstance(str_date, str):
            str_date = str_date[: 10]
            fecha = datetime.datetime.strptime(str_date, '%Y-%m-%d')
            fecha = datetime.date(fecha.year, fecha.month, fecha.day)

            return fecha

    registro_id = fields.Many2one('viatico.registro')

    employee_id = fields.Many2one('hr.employee', string='Empleado',
                                  required=True)
    job_id = fields.Many2one(related='employee_id.job_id', string='Posicion',
                             readonly=True)

    concepto_id = fields.Many2one('viatico.conceptos', string='Concepto',
                                  required=True)
    # tipo = fields.Selection(related='registro_id.tipo')
    # zonas_id = fields.Many2one(related='registro_id.zonas_id', string='Zona')
    # escala_id = fields.Many2one(related='registro_id.escala_id', string='Escala')

    pay_desayuno = fields.Boolean(defaulr=False, string='pagar desayuno?')
    pay_almuerzo = fields.Boolean(defaulr=False, string='pagar almuerzo?')
    pay_cena = fields.Boolean(defaulr=False, string='pagar cena?')
    pay_alojamiento = fields.Boolean(defaulr=False,
                                     string='pagar alojamiento?')
    pay_dia_completo = fields.Boolean(defaulr=False,
                                      string='pagar dia_completo?')
    pay_gasto_estra = fields.Boolean(default=False,
                                     string='pagar gastos Extraordinario?')
    pay_gasto_imp = fields.Boolean(default=False,
                                   string='pagar gastos impuesto?')

    desayuno = fields.Float(string='Monto Desayuno', readonly=True)
    almuerzo = fields.Float(string='Monto Almuerzo', readonly=True)
    cena = fields.Float(string='Monto Cena', readonly=True)
    alojamiento = fields.Float(string='Monto Alojamiento', readonly=True)
    dia_completo = fields.Float(string='Monto Dia Completo', readonly=True)
    gasto_estra = fields.Float(string='Monto Gastos Extras', readonly=True)
    gasto_imp = fields.Float(string='Monto Gastos de Impuestos', readonly=True)

    monto_total = fields.Float(string='Total')

    @api.onchange('employee_id')
    def _onchange_employee(self):

        if self.job_id:
            categorias = self.env['viatico.categoria'].search(
                [('escala_id', '=', self.registro_id.escala_id.id),
                 ('zona_id', '=', self.registro_id.zonas_id.id)])

            categoria_id = None
            for categoria in categorias:
                for trabajo in categoria.puesto_trabajo:
                    if trabajo.id == self.job_id.id:
                        categoria_id = categoria.id
                        break

            if categoria_id:
                concepto = self.env['viatico.conceptos'].search(
                    [('categ_id', '=', categoria_id),
                     ('tipo', '=', self.registro_id.tipo)])

                self.concepto_id = concepto.id

    @api.onchange('pay_desayuno', 'pay_almuerzo', 'pay_cena', 'pay_alojamiento',
                  'pay_gasto_estra', 'pay_gasto_imp', 'pay_dia_completo')
    def _onchange_pay(self):
        desde= self.str_to_datetime(self.registro_id.fecha_viaje_desde)
        hasta= self.str_to_datetime(self.registro_id.fecha_viaje_hasta)

        temp = hasta - desde

        dias = temp.days if temp.days >= 1 else 1

        if self.pay_desayuno:
            self.desayuno = self.concepto_id.desayuno * dias
        else:
            self.desayuno = 0

        if self.pay_almuerzo:
            self.almuerzo = self.concepto_id.almuerzo * dias
        else:
            self.almuerzo = 0

        if self.pay_cena:
            self.cena = self.concepto_id.cena * dias
        else:
            self.cena = 0

        if self.pay_alojamiento:
            self.alojamiento = self.concepto_id.alojamiento * dias
        else:
            self.alojamiento = 0

        if self.pay_gasto_estra:
            self.gasto_estraordinario = self.concepto_id.gasto_estraordinario * dias
        else:
            self.gasto_estraordinario = 0

        if self.pay_gasto_imp:
            self.gasto_impuesto = self.concepto_id.gasto_impuesto * dias
        else:
            self.gasto_impuesto = 0

        if self.pay_dia_completo:
            self.dia_completo = self.concepto_id.dia_completo * dias
        else:
            self.dia_completo = 0

        if not self.pay_desayuno:
            self.desayuno = 0
        if not self.pay_almuerzo:
            self.almuerzo = 0
        if not self.pay_cena:
            self.cena = 0
        if not self.pay_alojamiento:
            self.alojamiento = 0
        if not self.pay_dia_completo:
            self.dia_completo = 0
        if not self.pay_gasto_estra:
            self.gasto_estraordinario = 0
        if not self.pay_gasto_imp:
            self.gasto_impuesto = 0

    @api.model
    def create(self, values):
        # Rellenando los valores que son READONLY
        # pdb.set_trace()
        registro = self.env['viatico.registro'].browse(values['registro_id'])
        desde= self.str_to_datetime(registro.fecha_viaje_desde)
        hasta= self.str_to_datetime(registro.fecha_viaje_hasta)

        temp = hasta - desde

        dias = temp.days if temp.days >= 1 else 1

        concepto_id = self.env['viatico.conceptos'].browse(
            values['concepto_id'])

        if values['pay_desayuno']:
            values['desayuno'] = concepto_id.desayuno * dias
        if values['pay_almuerzo']:
            values['almuerzo'] = concepto_id.almuerzo * dias
        if values['pay_cena']:
            values['cena'] = concepto_id.cena * dias
        if values['pay_alojamiento']:
            values['alojamiento'] = concepto_id.alojamiento * dias
        if values['pay_dia_completo']:
            values['dia_completo'] = concepto_id.dia_completo * dias
        if values['pay_gasto_estra']:
            values['gasto_estra'] = concepto_id.gasto_estraordinario * dias
        if values['pay_gasto_imp']:
            values['gasto_imp'] = concepto_id.gasto_impuesto * dias
        return super(RegistroDeViaticosLines, self).create(values)

    @api.multi
    def write(self, values, context=None):

        registro = self.env['viatico.registro'].browse(self.registro_id.id)
        desde = self.str_to_datetime(registro.fecha_viaje_desde)
        hasta = self.str_to_datetime(registro.fecha_viaje_hasta)

        temp = hasta - desde

        dias = temp.days if temp.days >= 1 else 1
        concepto_id = self.env['viatico.conceptos'].browse(
            self.concepto_id.id)

        if 'pay_desayuno' in values:
            if values['pay_desayuno'] == True:
                values['desayuno'] = concepto_id.desayuno * dias
            else :
                values['desayuno'] = 0
        if 'pay_almuerzo' in values:
            if values['pay_almuerzo'] == True:
                values['almuerzo'] = concepto_id.almuerzo * dias
            else :
                values['almuerzo'] = 0
        if 'pay_cena' in values:
            if values['pay_cena'] == True:
                values['cena'] = concepto_id.cena * dias
            else :
                values['cena'] = 0
        if 'pay_alojamiento' in values:
            if values['pay_alojamiento'] == True:
                values['alojamiento'] = concepto_id.alojamiento * dias
            else :
                values['alojamiento'] = 0
        if 'pay_dia_completo' in values:
            if values['pay_dia_completo'] == True:
                values['dia_completo'] = concepto_id.dia_completo * dias
            else :
                values['dia_completo'] = 0
        if 'pay_gasto_estra' in values:
            if values['pay_gasto_estra'] == True:
                values['gasto_estra'] = concepto_id.gasto_estraordinario * dias
            else :
                values['gasto_estra'] = 0
        if 'pay_gasto_imp' in values:
            if values['pay_gasto_imp'] == True:
                values['gasto_imp'] = concepto_id.gasto_impuesto * dias
            else :
                values['gasto_imp'] = 0
        return super(RegistroDeViaticosLines, self).write(values)