# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class AccountStatusReport(models.Model):

    _name = "report.account.analytics"
    _auto = False
    _description = "Account Analytics Report"
    _rec_name = 'id'

    name = fields.Char('Number',readonly="True")
    partner_id = fields.Many2one('res.partner', readonly=True)
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True)
    invoice_date_due = fields.Date(string='Due Date', readonly=True)
    l10n_latam_document_type_id = fields.Many2one("l10n_latam.document.type", "Document Type", readonly=True)
    l10n_do_fiscal_number = fields.Char("Fiscal Number", readonly=True)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    move_type = fields.Selection(selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),
        ], string='Type', readonly=True)
    
    company_id = fields.Many2one(comodel_name='res.company', string='Company',readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True, string='Currency')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')

    amount_untaxed_signed = fields.Monetary(string='Untaxed Amount Signed', readonly=True,
                            currency_field='company_currency_id')
    amount_tax_signed = fields.Monetary(string='Tax Signed', readonly=True,
                            currency_field='company_currency_id')
    amount_total_signed = fields.Monetary(string='Total Signed', readonly=True,
                            currency_field='company_currency_id')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', readonly=True,
                            currency_field='company_currency_id')
    amount_tax = fields.Monetary(string='Tax', readonly=True,
                            currency_field='company_currency_id')
    amount_total = fields.Monetary(string='Total', readonly=True,
                            currency_field='company_currency_id')
    payment_state = fields.Selection( [
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
            ('reversed', 'Reversed'),
            ('invoicing_legacy', 'Invoicing App Legacy'),
        ], string="Payment Status",readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)

    def _select(self):
        return """
          SELECT AM.ID, 
                AM.NAME,
                AM.COMPANY_ID,
                AM.CURRENCY_ID,
                AM.PARTNER_ID,
                AM.L10N_LATAM_DOCUMENT_TYPE_ID,
                AM.L10N_DO_FISCAL_NUMBER,
                AM.INVOICE_DATE,
                AM.INVOICE_DATE_DUE,
                AM.STATE,
                AM.MOVE_TYPE,
                AM.AMOUNT_UNTAXED_SIGNED,
                AM.AMOUNT_TAX_SIGNED,
                AM.AMOUNT_TOTAL_SIGNED,
                AM.AMOUNT_UNTAXED,
                AM.AMOUNT_TAX,
                AM.AMOUNT_TOTAL,
                AM.PAYMENT_STATE,
                AM.JOURNAL_ID
        """

    def _from(self):
        return """
            FROM ACCOUNT_MOVE AS AM
        """

    def _join(self):
        return """
        """

    def _where(self):
        return """
                   WHERE AM.MOVE_TYPE in ('in_invoice','out_invoice')
                """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where())
        )