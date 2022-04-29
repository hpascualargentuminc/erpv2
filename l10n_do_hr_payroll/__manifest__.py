# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Argentum - Nómina',
    'icon': '/l10n_do_hr_payroll/static/description/icon.png',
    'category': 'Payroll',
    'depends': ['hr_payroll', 'account_accountant',],
    'version': '1.0',
    'description': "Reglas de Nómina de República Dominicana.",
    'data': [
        'views/hr_contract.xml',
        'data/hr_payroll_structure_type.xml',
        'data/hr_payroll_structure.xml',
        'data/hr_salary_rule_category.xml',
        'data/hr_rule_parameter.xml',
        'data/hr_salary_rule1.xml',
        'data/hr_salary_rule2.xml',
        'data/hr_payslip_input_type.xml',
    ],
    'auto_install': False,
}
