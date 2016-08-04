{
    'name': "cjc_request",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ramon Caraballo",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'marcos_cjc', 'account_voucher'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'sequence.xml',
        'templates.xml',
        'cjc_request_limit.xml',
        'ext_account_voucher.xml',
        'extends_bank_statement.xml',
        'report/cjc_request_report.xml',
        'wizard/wizard.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
# -*- coding: utf-8 -*-
