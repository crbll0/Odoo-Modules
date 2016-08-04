# -*- coding: utf-8 -*-
{
    'name': "adrRealizarDepos",

    'summary': """
        Extiende el modelo deposit.ticket""",

    'description': """
        Agregas un nuevo estado "Auditado" y Las Etapas
    """,

    'author': "Ramon Caraballo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'npg_account_make_deposit'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}