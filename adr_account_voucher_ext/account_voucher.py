
from openerp.osv import fields, osv


class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    _columns = {
        'state': fields.selection(
            (
                ('draft', 'Borrador'),
                ('validado', 'Validado'),
                ('cancel', 'Cancelado'),
                ('auditoria', 'Auditoria'),
                ('financiero', 'Financiero'),
                ('ejecutar_pago', 'Ejecutar Pago'),
                ('proforma', 'Pro-forma'),
                ('posted', 'Contabilizado'),
            ), 'State'),

        'stage':  fields.selection(
            (
                ('draft', 'Esperando Validacion'),
                ('validado', 'Esperando Confirm. Auditoria'),
                ('auditoria', 'Esperando Confirm. de Financiero'),
                ('financiero', 'Listo para Ejecutar el pago'),
                ('ejecutar_pago', 'Esperando para Contabilizar'),
                ('proforma', 'Pro-forma'),
                ('posted', 'Contabilizado'),
            ), 'Stage', default='draft'),

        'confirmado_por': fields.many2one('res.users', 'Confirmado por',
                                          readonly=True),
        'auditoria_por': fields.many2one('res.users', 'Confirmacion de Auditoria por',
                                         readonly=True),
        'financiero_por': fields.many2one('res.users', 'Confirmacion de Financiero por',
                                          readonly=True),
        'ejecutado_por': fields.many2one('res.users', 'Ejecutado por', readonly=True),
        'cancelado_por': fields.many2one('res.users', 'Cancelado', readonly=True),
        }


    def button_contirmar(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'validado', 'confirmado_por': uid})
        return True

    def button_auditoria(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'auditoria', 'stage': 'auditoria',
                                  'auditoria_por': uid})
        return True

    def button_financiero(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'financiero', 'stage': 'financiero',
                                  'financiero_por': uid})
        return True

    def button_ejecutar_pago(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'ejecutar_pago', 'stage': 'ejecutar_pago',
                                  'ejecutado_por': uid})
        return True
