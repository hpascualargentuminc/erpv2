import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # ESTE ARCHIVO SE DEJA COMO UN CASCARÓN PARA TOMAR FUNCIONES DE NCF MANAGER SI SON NECESARIAS

    is_company_currency = fields.Boolean(compute=_is_company_currency)

    invoice_rate = fields.Monetary(
        string="Tasa", compute=_get_rate, currency_field="currency_id"
    )

    @api.depends("currency_id", "date_invoice")
    def _get_rate(self):
        for inv in self:
            if not inv.is_company_currency:
                try:
                    rate = inv.currency_id.with_context(
                        dict(self._context or {}, date=inv.date_invoice)
                    )
                    inv.invoice_rate = 1 / rate.rate
                    inv.rate_id = rate.res_currency_rate_id
                except (Exception) as err:
                    _logger.debug(err)

    
    @api.depends("currency_id")
    def _is_company_currency(self):
        for inv in self:
            if inv.currency_id == inv.company_id.currency_id:
                inv.is_company_currency = True
            else:
                inv.is_company_currency = False

    def action_invoice_cancel(self):

        fiscal_invoices = self.filtered(
            lambda inv: inv.company_id.country_id.code == "DO"
            and inv.journal_id.ncf_control
        )
        if fiscal_invoices and not self.env.user.has_group(
            "ncf_manager.group_l10n_do_fiscal_invoice_cancel"
        ):
            raise AccessError("No tiene permitido cancelar Facturas Fiscales")

        return super(AccountInvoice, self).action_invoice_cancel()
