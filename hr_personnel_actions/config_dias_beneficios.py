# -*- coding: utf-8 -*-
import logging
import pdb

from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)


class DiasBeneficios(osv.osv):
    _name = 'dias.beneficios'

    _columns = {
        'preaviso_3': fields.integer('Dias de Preaviso de 3 a 6 Meses', default=7),
        'preaviso_7': fields.integer('Dias de Preaviso de 7 a 11 Meses', default=14),
        'preaviso_12': fields.integer('Dias de Preaviso Mayor a 1 año', default=28),

        'cesantia_3': fields.integer('Dias de Cesantia de 3 a 6 Meses', default=6),
        'cesantia_7': fields.integer('Dias de Cesantia de 7 a 11 Meses', default=13),
        'cesantia_12': fields.integer('Dias de Cesantia Mayor a 1 año', default=21),
        'cesantia_5': fields.integer('Dias de Cesantia Mayor a 5 año', default=23),

        # 'salario_minimo': fields.float('Salario Minimo'),
    }

    def create(self, cr, uid, ids, context=None):
        total_registro = self.search(cr, uid, [(1, '=', 1)])

        if len(total_registro) >= 1:
            raise osv.except_osv('Error',
                                 'El numero Maximo de registro es 1 (" UNO "),'
                                 'Elimina o Modifica el registro existente.')
        else:
            super(DiasBeneficios, self).create(cr, uid, ids, context)

DiasBeneficios()
