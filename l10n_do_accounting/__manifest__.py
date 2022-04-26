{
    "name": "Fiscal Accounting (Rep. Dominicana)",
    "summary": """
        Este módulo extiende las capacidades contables para el cumplimento de la norma 06-18 de la
         Dirección de Impuestos Internos en la República Dominicana.""",
    "author": "Argentum Inc S.R.L.",
    "category": "Localization",
    # any module necessary for this one to work correctly
    "depends": ["l10n_latam_invoice_document", "l10n_do"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "wizard/account_move_reversal_views.xml",
        "wizard/account_move_cancel_views.xml",
        "wizard/account_debit_note_views.xml",
        "wizard/account_expiration_date_update_wizard_views.xml",
        "views/res_config_settings_view.xml",
        "views/account_move_views.xml",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/account_dgii_menuitem.xml",
        "views/account_journal_views.xml",
        "views/l10n_latam_document_type_views.xml",
        "views/report_templates.xml",
        "views/report_invoice.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
