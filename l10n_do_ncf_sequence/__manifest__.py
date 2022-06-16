# -*- coding: utf-8 -*-
{
    'name': "Generador Secuencias de NCFs",

    'summary': "Generador de Secuencias de NCFs para la Rep. Dominicana",

    'description': "",

    'author': "Argentum Inc",
    'website': "https://www.argentuminc.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_do_accounting', 'l10n_latam_invoice_document'],

    # always loaded
    'data': [
        'data/ir.sequence.csv',
        'data/l10n_latam.document.type.csv',
        'views/ir_sequence_view.xml',
        'views/l10n_latam_document_type_view.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings.xml',
        'security/ir.model.access.csv',
    ],

}
