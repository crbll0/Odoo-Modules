# -*- coding: utf-8 -*-

import logging
from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)


class AccionesEmpleados(osv.osv):

    _inherit = 'res.partner'

    def set_antiguedad_label(self, cr, uid,):

        contra_obj = self.pool.get('hr.contract')

        # Lista de IDs de todos los empleados.
        empleados_ids = self.search(cr, uid, [(1, '=', 1)])

        hoy = datetime.date.today()

        for empleado_id in empleados_ids:

            try:
                # Obtiene el contrato mas Antiguo del Empleado.
                contra_id = contra_obj.search(
                    cr, uid, [('employee_id', '=', empleado_id)],
                    order='date_start')[0]

            except IndexError:
                continue

            # if contra_id:
            contra_viejo = contra_obj.browse(cr, uid, contra_id).date_start

            # Convertir la fecha tipo STR a tipo DATETIME
            fecha = datetime.datetime.strptime(contra_viejo, '%Y-%m-%d')
            fecha = datetime.date(fecha.year, fecha.month, fecha.day)

            dias = (hoy - fecha).days
            anios = dias / 365

            # ID de la Etiqueta de Antiguedad que le corresponde
            # segun la fecha del contrato mas antigup del empleado.
            etiqueta_id = 2 if anios <= 5 else 3 if anios <= 10 else 4

            etiquetas_empl = self.browse(cr, uid, empleado_id).category_ids
            etiquetas_ids = [etiqueta.id for etiqueta in etiquetas_empl]

            if etiqueta_id not in etiquetas_ids:
                # Remover las Etiquetas de Antiguedad anteriores.
                update = [et for et in etiquetas_ids if et not in [2, 3, 4]]
                update.append(etiqueta_id)

                self.write(cr, uid, empleado_id,
                           {'category_ids': [(6, 0, update)]})
        return True

    def set_tarifa_venta(self, cr, uid):
        empl = self.pool.get('hr.employee')
        ids = empl.search(cr, uid, [(1, '=', 1)])

        employee_ids = empl.browse(cr, uid, ids)

        # Las KEY son los ID de las Companias y los VALUE son los ID de
        # las cuentas CUENTA POR COBRAR FUNC.Y EMPLEADOS
        # Cuando se le pasa la KEY de la compania devuelve el ID de la cuenta
        # CUENTA POR COBRAR FUNC.Y EMPLEADOS para esa compania.
        cuanta_compania = {
            25: 12660, 23: 9140, 9: 7732, 29: 6676, 7: 4564, 1: 3510, 31: 3860,
            26: 4916, 17: 5268, 24: 6324, 16: 5972, 10: 7028, 22: 7380, 28: 8436,
            12: 8084, 3: 8788, 15: 9492, 20: 5620, 6: 10196, 14: 10548, 19: 9844,
            21: 11252, 8: 11604, 13: 10900, 4: 11956, 18: 12308, 5: 13012, 11: 4212,
        }

        for num, employee in enumerate(employee_ids):
            partner_id = employee.address_home_id.id
            if partner_id:
                # partner = self.browse(cr, uid, partner_id)

                company_id = empl.browse(cr, uid, employee.id).company_id.id

                self.write(cr, uid, partner_id, {'property_product_pricelist': 10,
                                                 'property_payment_term': 3})

                if company_id:
                    self.write(cr, uid, partner_id, {
                        'property_account_receivable': cuanta_compania[company_id]
                    })

        return True

    def set_plazo_estudiante(self, cr, uid):
        estudiantes_ids = self.search(cr, uid, [('estudiante', '=', True)])
        estudiantes = self.browse(cr, uid, estudiantes_ids)

        for num, estudiante in enumerate(estudiantes):
            if estudiante.property_payment_term.id != 3:
                self.write(cr, uid, estudiante.id, {'property_payment_term': 3})

        return True

    def several_sets(self, cr, uid):
        limit = 10
        ids = self.search(cr, uid, [(1, '=', 1)])

        partners = self.browse(cr, uid, ids)

        list_ids = []

        for n, partner in enumerate(partners):
            account = [False, ]
            journal = [False, ]
            _logger.info('Por el : %d de %d' % (n, len(partners)))

            if partner.company_id.id:
                account = self.pool.get('account.account').search(
                    cr, uid, [('name', '=like', 'OTRAS CUENTAS POR COBRAR(INSTITUCIONES ALIADAS)'),
                              ('company_id', '=', partner.company_id.id)])

                _search = 'Efectivo' if partner.company_id.id != 1 else 'Caja General (CONTADO)'

                journal = self.pool.get('account.journal').search(
                    cr, uid, [('name', '=like', _search),
                              ('company_id', '=', partner.company_id.id)])
            if limit == 0:
                break

            if not partner.property_payment_term.id:
                limit -= 1
                _logger.info('ID: %d' % partner.id)
                _logger.info('account: %s' % account)
                _logger.info('journal: %s' % journal)
                self.write(cr, uid, partner.id,
                           {'property_account_receivable': account[0],
                            'property_payment_term': 1,
                            'customer_payment_method': journal[0],
                            })


class Activos(osv.osv):

    _inherit = 'account.asset.asset'

    def fix_name(self, cr, uid):
        special = {
            u'á': 'a', u'Á': 'A',
            u'é': 'e', u'É': 'E',
            u'í': 'i', u'Í': 'I',
            u'ó': 'o', u'Ó': 'O',
            u'ú': 'u', u'Ú': 'U',
            u'ñ': 'n', u'Ñ': 'N',
        }

        assets_ids = self.search(cr, uid, [(1, '=', 1)])
        p = self.pool.get('product.template')
        product_ids = p.search(cr, uid, [(1, '=', 1)])

        assets = self.browse(cr, uid, assets_ids)
        products = p.browse(cr, uid, product_ids)

        for num, asset in enumerate(assets):
            name = asset.name
            for letter in special.keys():
                if letter in asset.name:
                    new_name = name.replace(letter, special[letter])
                    _logger.info('{} de {}'.format(num, len(product_ids)))
                    self.write(cr, uid, asset.id, {'name': new_name})

        for num, product in enumerate(products):
            # name = product.name
            for letter in special.keys():
                if letter in product.name:
                    new_name = product.name.replace(letter, special[letter])

                    _logger.info('{}|{} de {}'.format(product.id,
                                                      num, len(product_ids)))
                    p.write(cr, uid, product.id, {'name': new_name})

        return True
