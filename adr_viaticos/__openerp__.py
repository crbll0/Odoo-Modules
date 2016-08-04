{
    'name': "adrViaticos",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ramon Caraballo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'cjc_request'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'secuencia.xml',

        'views/categoria_view.xml',
        'views/registro_viaticos_view.xml',
        'views/zonas_view.xml',
        'views/escala_view.xml',
        'views/concepto_view.xml',
        'ext_cjc_request/ext_cjc_request.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
# -*- coding: utf-8 -*-
