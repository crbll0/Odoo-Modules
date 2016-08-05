# -*- coding: utf-8 -*-
{
    'name': "ADR Contratos Ventas",

    'summary': """
        Extiende y/o da nueva funcionalidad a los contratos de ventas.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ramon Caraballo",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_analytic_analysis'],

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