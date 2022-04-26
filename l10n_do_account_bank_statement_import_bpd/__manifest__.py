# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Importación de Estados Bancarios - Banco Popular Dominicano',
    'author': "Argentum Inc. S.R.L.",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account_bank_statement_import'],
    'description': """
Módulo para importar estados bancarios en formato OFX -Money- para Banco Popular Dominicano.

    """,
    'data': [
        'wizard/account_bank_statement_import.xml',
    ],
    'installable': True,
    'auto_install': True,
}
