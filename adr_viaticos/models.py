# -*- coding: utf-8 -*-

import logging
import pdb
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class EscalasViaticos(models.Model):
    _name = 'viatico.escala'

    name = fields.Char(string='Escala')


class ZonasViaticos(models.Model):
    _name = 'viatico.zonas'

    name = fields.Char(string='Zona')
    escala_id = fields.Many2one('viatico.escala', string='Escala')
    vehiculos_ids = fields.One2many('viatico.zonas.linea_peaje', 'zona_id')


class ZonasVehiculoPeajeLine(models.Model):
    _name = 'viatico.zonas.linea_peaje'

    zona_id =fields.Many2one('viatico.zonas')
    vehiculo_id = fields.Many2one('fleet.vehicle', string='Vehiculo')
    peaje = fields.Float(string='Peaje')


class CategoriasViaticos(models.Model):
    _name = 'viatico.categoria'

    name = fields.Char(string='Categoria')
    puesto_trabajo = fields.Many2many(
        'hr.job', 'viatico_categoria_job_rel', 'job'
    )
    escala_id = fields.Many2one('viatico.escala', string='Escala')
    zona_id = fields.Many2one('viatico.zonas', string='Zona')

    @api.onchange('escala_id')
    def _onchange_escala(self):
        zonas = self.env['viatico.zonas'].search([
            ('escala_id', '=', self.escala_id.id)])
        if zonas:
            value = [x.id for x in zonas]
            self.zona_id = False
            return {'domain': {'zona_id': [('id', 'in', value)]}}

    @api.model
    def create(self, values):
        if values['escala_id']:
            escala_name = self.env['viatico.escala'].browse(
                values['escala_id']).name
            values['name'] += '/' + escala_name
            if values['zona_id']:
                zona_name = self.env['viatico.zonas'].browse(
                    values['zona_id']).name
                values['name'] += '/' + zona_name

        return super(CategoriasViaticos, self).create(values)


class ConceptosViaticos(models.Model):
    _name = 'viatico.conceptos'

    categ_id = fields.Many2one('viatico.categoria', 'Categoria', required=True)

    name = fields.Char(string='Name', store=True)

    desayuno = fields.Float()
    almuerzo = fields.Float()
    cena = fields.Float()
    alojamiento = fields.Float()
    dia_completo = fields.Float()

    gasto_estraordinario = fields.Float()
    gasto_impuesto = fields.Float()

    tipo = fields.Selection((('viatico', 'Viatico'), ('dieta', 'Dieta')),
                            default='viatico')
    @api.model
    def create(self, values):
        cat = self.env['viatico.categoria'].browse(values['categ_id'])
        name = "Concepto/{tipo}/{esc}/{zon}".format(tipo=values['tipo'],
                                                   esc=cat.escala_id.name,
                                                   zon=cat.zona_id.name)
        values['name'] = name
        
        return super(ConceptosViaticos, self).create(values)