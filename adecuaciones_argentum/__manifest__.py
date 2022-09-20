{
    "name": "Adecuaciones Argentum.",
    "summary": """
        Adecuaciones para Argentum""",
    "author": "ARGENTUM Inc S.R.L.",
    "category": "Base",
    "version": "15",
    # any module necessary for this one to work correctly
    "depends": ["contacts", "base", "sale_management", "sale_crm", "account", "account_accountant", "l10n_do_accounting"],
    # always loaded
    "data": [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/bank_statement_form.xml',
        'report/report_invoice.xml',
        'views/project_task_views.xml',
        'views/crm_lead_views.xml',
        'views/account_status_report.xml',
        'views/res_partner_views.xml'
    ],
    
}
