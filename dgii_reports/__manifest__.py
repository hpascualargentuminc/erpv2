{
    "name": "Declaraciones DGII",
    "summary": """
        Este módulo extiende las funcionalidades de generación de comprobantes fiscales (l10n_do_ncf_sequence),
        integrando los reportes de declaraciones fiscales""",
    "author": "ARGENTUM Inc S.R.L.",
    "category": "Accounting",
    "version": "15",
    # any module necessary for this one to work correctly
    "depends": ["base", "l10n_do_ncf_sequence"],
    # always loaded
    "data": [
        "data/ir_config_parameter_data.xml",
        "data/invoice_service_type_detail_data.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/res_partner_views.xml",
        "views/account_account_views.xml",
        "views/account_invoice_views.xml",
        "views/dgii_report_views.xml",
        "wizard/dgii_report_regenerate_wizard_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'dgii_reports/static/src/less/dgii_reports.css',
            'dgii_reports/static/src/js/widget.js',
        ],
    },
}
