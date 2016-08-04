# -*- coding: utf-8 -*-
{
    'name': "adrMessageTags",

    'summary': """
        Agrega el Campo de Tag a la composicion de los mensajes.""",

    'description': """ """,

    'author': "Ramon Caraballo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/models_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}