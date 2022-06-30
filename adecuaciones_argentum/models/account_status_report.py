# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class AccountStatusReport(models.Model):

    _name = "report.account.analytics"
    _auto = False
    _description = "Analisis de Entradas y Salidas"
    _rec_name = 'id'

    name = fields.Char(u'Número de Comprobante',readonly="True")
    partner_id = fields.Many2one('res.partner', readonly=True,string="Empresa")
    invoice_date = fields.Date(string='Fecha de Factura', readonly=True)
    invoice_date_due = fields.Date(string='Fecha de Vencimiento', readonly=True)
    l10n_latam_document_type_id = fields.Many2one("l10n_latam.document.type", "Tipo de Comprobante", readonly=True)
    l10n_do_fiscal_number = fields.Char("Comprobante Fiscal", readonly=True)
    state = fields.Selection(selection=[
            ('draft', 'Borrador'),
            ('posted', 'Publicado'),
            ('cancel', 'Cancelado'),
        ], string='Status', readonly=True)
    move_type = fields.Selection(selection=[
            ('entry', 'Entrada'),
            ('out_invoice', 'Factura de Cliente'),
            ('out_refund', 'Nota de Crédito'),
            ('in_invoice', 'Factura de Proveedor'),
            ('in_refund', 'Nota de Débito'),
            ('out_receipt', 'Recibo de Venta'),
            ('in_receipt', 'Recibo de Compra'),
        ], string='Type', readonly=True)
    
    company_id = fields.Many2one(comodel_name='res.company', string=u'Compañia',readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True, string='Moneda')
    company_currency_id = fields.Many2one(string='Moneda Compañia', readonly=True, related='company_id.currency_id')

    amount_untaxed_signed = fields.Monetary(string='Total sin Impuestos', readonly=True,
                            currency_field='company_currency_id')
    amount_tax_signed = fields.Monetary(string='Impuestos', readonly=True,
                            currency_field='company_currency_id')
    amount_total_signed = fields.Monetary(string='Total', readonly=True,
                            currency_field='company_currency_id')
    
    payment_state = fields.Selection( [
            ('not_paid', 'No Pagado'),
            ('in_payment', 'En Proceso de Pago'),
            ('paid', 'Pagado'),
            ('partial', 'Pagado Parcial'),
            ('reversed', 'Reversado'),
            ('invoicing_legacy', 'Invoicing App Legacy'),
        ], string="Estado de Pago",readonly=True)
    journal_id = fields.Many2one('account.journal', string='Diario', readonly=True)

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