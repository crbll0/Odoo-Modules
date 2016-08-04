# -*- coding: utf-8 -*-

import pdb

from openerp import models, fields, api
from openerp.exceptions import Warning


class CajaChicaRequest(models.Model):

    _name = 'cjc_request.cjc_request'

    @api.one
    @api.depends('total', 'monto_solicitado')
    def _calc_diferencia(self):
        if self.monto_solicitado:
            result = self.total - self.monto_solicitado
            self.diferencia = result
            return float(result)

    def _get_login_user(self):
        print self.env.uid

        return self.env.uid

    def _computed_get_limit(self):
        company = self.env['res.users'].browse(self.env.uid).company_id.id

        diario_caja = self.env['account.journal'].search(
            [('active', '=', True), ('is_cjc', '=', True),
             ('company_id', '=', company)]
        )

        limite = self.env['cjc_request.cjc_limit'].search(
            [('company_id', '=', company), ('caja', '=', diario_caja.id)]).limite

        return limite
        # pass

    name = fields.Char(string='Secuencia', readonly=True)
    usuario = fields.Many2one('res.users', string='Usuario', required=True,
                              default=_get_login_user)
    departamento = fields.Many2one('hr.department', string='Departamento',
                                   required=True)
    monto_solicitado = fields.Float(string='Monto Solicitado', required=True)
    monto_solicitado2 = fields.Float(related='monto_solicitado')
    diferencia = fields.Float(compute='_calc_diferencia', store=True)
    concepto = fields.Text(string='Concepto', required=True)
    notas = fields.Text(string='Notas')

    caja_id = fields.Many2one('account.bank.statement', string='Caja')

    balance = fields.Float(related='caja_id.balance_end', string='Balance', store=True)

    limite_caja = fields.Float(default=_computed_get_limit, readonly=True,
                               string='Limite de Solicitud', store=True)

    journal_id = fields.Many2one('account.journal')
    period_id = fields.Many2one('account.period')

    cjc_line = fields.One2many('cjc_request.cjc_line', 'cjc_id',
                               string='Linea Caja Chica')
    total = fields.Float(readonly=True)

    state = fields.Selection((
        ('solic', 'Solicitado'), ('validar1','Validado'), ('aprobacion', 'Aprobar'),
        ('aprob', 'Aprobado'), ('entrega', 'Entregado'), ('recibido', 'Recibido'),
        ('auditoria', 'Auditoria'), ('done', 'Completado'), ('cancel', 'Cancelado')
    ), 'Estado', default='solic')

    stage = fields.Selection((
        ('solic', 'Esperando Validacion'), ('validar1', 'Esperando Aprobacion'),
        ('aprob', 'Esperando Entrega'), ('entrega', 'Esperando a ser Recibido'),
        ('recibido', 'Esperando Facturas'), ('rec_fact', 'Esperando para ser Auditado'),
        ('auditoria', 'Completado'),
    ), 'Etapa', default='solic')

    solicitado_por = fields.Many2one('res.users', string='Solicitado por', readonly=True)
    validado1_por = fields.Many2one('res.users', string='Validacion Encargado por', readonly=True)
    aprobado_por = fields.Many2one('res.users', string='Aprobado por', readonly=True)
    entregado_por = fields.Many2one('res.users', string='Entregadoo por', readonly=True)
    recibido_por = fields.Many2one('res.users', string='Recibido por', readonly=True)
    rec_fact_por = fields.Many2one('res.users', string='Recibio factura', readonly=True)
    validado_por = fields.Many2one('res.users', string='Validado por', readonly=True)
    auditado_por = fields.Many2one('res.users', string='auditado por', readonly=True)
    completado_por = fields.Many2one('res.users', string='completado por', readonly=True)
    cancelado_por = fields.Many2one('res.users', string='Cancelado por', readonly=True)

    @api.onchange('usuario')
    def get_department(self):
        if self.usuario:
            self.departamento = self.env['hr.employee'].search(
                [('user_id', '=', self.usuario.id)]).department_id.id or False

    @api.onchange('caja_id')
    def onchange_caja_id(self):
        self.journal_id = self.caja_id.journal_id.id

    @api.one
    def aprobar(self):
        self.write({'state': 'aprob', 'stage': 'aprob','aprobado_por': self.env.uid})

    @api.one
    def entrega(self):
        self.write({'state': 'entrega', 'stage': 'entrega',
                    'entregado_por': self.env.uid})

    @api.one
    def validar1(self):
        self.write({'state': 'validar1', 'stage': 'validar1',
                    'validado1_por': self.env.uid})

    @api.multi
    def registrar(self):
        view_id = self.env['ir.model.data'].get_object_reference(
            'cjc_request', 'cjc_request_wizard_view_form')[1]

        wizard = {
            'name': 'Gasto Caja Chica',
            'view_mode': 'form',
            'view_id': False,
            'views': [(view_id, 'form')],
            'view_type': 'form',
            'res_model': 'cjc_request.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }
        return wizard

    @api.one
    def rec_fact(self):

        if self.monto_solicitado > self.total:
            raise Warning('Aun quedan Facturas Pendientes por registrar para cumplir el monto solicitado.')

        self.write({'state': 'auditoria', 'stage': 'rec_fact',
                    'rec_fact_por': self.env.uid})
        return True

    @api.one
    def validar(self):
        self.write({'state': 'validar', 'stage': 'validar',
                    'validado_por': self.env.uid})

    @api.one
    def auditar(self):
        self.write({'state': 'done', 'stage': 'auditoria',
                    'auditado_por': self.env.uid, 'completado_por': self.env.uid})

    @api.one
    def aprobacion(self):
        self.state = 'aprobacion'
        
    @api.one
    def recibido(self):
        self.write({'state': 'recibido', 'stage': 'recibido',
                    'recibido_por': self.env.uid})
    
    @api.one
    def done(self):
        self.write({'state': 'done', 'stage': 'done'})
    
    @api.one
    def cancel(self):
        self.write({'state': 'cancel', 'cancelado_por': self.env.uid})

    @api.model
    def create(self, values):

        if self.tipo == 'cjc':
            limite_caja = self._computed_get_limit()
            if limite_caja and limite_caja < values['monto_solicitado']:
                raise Warning('El monto Solicitado no puede superar el Limite de solicitud')

            vals = super(CajaChicaRequest, self).create(values)
            vals['solicitado_por'] = self.env.uid
            vals['name'] = self.env['ir.sequence'].get(
                'cjc_request.cjc_request')

        else:
            vals = super(CajaChicaRequest, self).create(values)
            vals['name'] = self.env['ir.sequence'].get(
                'cjc_request.cjc_request')

        return vals

    @api.multi
    def write(self, values):
        obj = self.browse(self._ids)
        mongo_guardado = self.browse(self._ids).monto_solicitado
        monto_solicitado = values['monto_solicitado'] if 'monto_solicitado' in values else mongo_guardado
        # Cuando se elije caja por primera vez.
        if 'caja_id' in values:
            balance = self.env['account.bank.statement'].browse(
                values['caja_id']).balance_end

            if balance < monto_solicitado:
                raise Warning('El monto soliciado no puede superar el Balance de caja')

        # Si el objeto ya esta guardado y se quiere modigicar el monto solicitado
        # cj_balance = self.balance if self.balance else obj.caja_id.balance_end
        # if obj.caja_id and cj_balance < monto_solicitado:
        #     raise Warning('El monto soliciado no puede superar el Balance de caja')

        return super(CajaChicaRequest, self).write(values)


class CajaChicaLine(models.Model):
    _name = 'cjc_request.cjc_line'

    fecha = fields.Date(string='Fecha', readonly=True)
    comunicacion = fields.Char(string='Comunicacion', readonly=True)
    referencia = fields.Char(string='Referencia', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Compania', readonly=True)
    importe = fields.Float('Importe', readonly=True)
    cjc_id = fields.Many2one('cjc_request.cjc_request', string='Caja Chica')


class CajaChicaRequestLimit(models.Model):
    _name = 'cjc_request.cjc_limit'

    caja = fields.Many2one('account.journal', string='Caja')

    limite = fields.Float(string='Limite de Caja')

    company_id = fields.Many2one('res.company', string='Compañia')
