# -*- coding: utf-8 -*-
{
    'name': "API Product",

    'summary': """
        API pour recupérer les produits 
        """,

    'description': """
        API REST pour recupérer les sur un mobile
    """,

    'author': "Progistack",
    'website': "http://www.progistack.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'sequence': -190,

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'website_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
