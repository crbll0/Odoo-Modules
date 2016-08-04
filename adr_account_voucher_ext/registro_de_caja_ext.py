from openerp.osv import osv, fields


class RegistroCaja(osv.osv):
    _inherit = 'account.bank.statement'

    _columns = {
        'login_user': fields.char('Login', readonly=True),
    }

    def onchanve_userid(self, cr, uid, ids, user_id, context=None):

        if user_id:
            user = self.pool.get('res.users').browse(cr, uid, user_id)

            value = {'value': {'login_user': user.login},}

            return value

    def create(self, cr, uid, ids, context=None):
        login = self.onchanve_userid(cr, uid, ids, ids['user_id'])['value']
        ids['login_user'] = login['login_user']

        return super(RegistroCaja, self).create(cr, uid, ids, context)