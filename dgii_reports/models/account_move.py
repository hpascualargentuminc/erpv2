import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InvoiceServiceTypeDetail(models.Model):
    _name = "invoice.service.type.detail"
    _description = "Invoice Service Type Detail"

    name = fields.Char()
    code = fields.Char(size=2)
    parent_code = fields.Char()

    _sql_constraints = [
        ("code_unique", "unique(code)", _("Code must be unique")),
    ]


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoice_payment_widget(self):
        j = json.loads(self.invoice_payments_widget)
        return j["content"] if j else []

    def _compute_invoice_payment_date(self):
        for inv in self:
            if inv.payment_state == "paid":
                dates = [payment["date"] for payment in inv._get_reconciled_payments()]
                if dates:
                    max_date = max(dates)
                    date_invoice = inv.invoice_date
                    inv.payment_date = (
                        max_date if max_date >= date_invoice else date_invoice
                    )

    @api.constrains("tax_ids")
    def _check_isr_tax(self):
        """Restrict one ISR tax per invoice"""
        for inv in self:
            line = [
                tax_line.tax_id.purchase_tax_type
                for tax_line in inv.line_ids.tax_ids
                if tax_line.tax_id.purchase_tax_type in ["isr", "ritbis"]
            ]
            if len(line) != len(set(line)):
                raise ValidationError(
                    _("An invoice cannot have multiple" "withholding taxes.")
                )

    def _convert_to_local_currency(self, amount):
        # Como ahora tomo de los line_ids, el amount puede venir negativo o positivo, por lo cual los debo llevar siempre a positivo, excepto con las NC (ver a continación)
        sign = 1
        if amount < 0:
            sign = -1
        
        # Si es una nota de crédito, todos sus valores los debo poner negativos, siempre!
        if self.move_type in ["in_refund", "out_refund"]:
            if amount < 0:
                sign = 1
            else:
                sign = -1

        rate_date = self.date or self.invoice_date or fields.Date.today()
        if self.currency_id != self.company_id.currency_id:
            amount = self.currency_id._convert(
                amount, self.company_id.currency_id, self.company_id, rate_date
            )
        
        return amount * sign

    @api.depends("line_ids", "line_ids.amount_currency", "payment_state", "state")
    def _compute_taxes_fields(self):
        """Compute invoice common taxes fields"""
        for inv in self:
            
            # Solo me interesa los lines que son de tipo Impuesto.
            tax_line_ids = inv.line_ids.filtered(
                                lambda tax: bool(tax.tax_line_id)
                                )

            if inv.state != "draft":
                # Monto Impuesto Selectivo al Consumo
                inv.selective_tax = inv._convert_to_local_currency(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.tax_line_id.tax_group_id.name == "ISC"
                        ).mapped("amount_currency")
                    )
                )

                # Monto Otros Impuestos/Tasas
                inv.other_taxes = inv._convert_to_local_currency(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.tax_line_id.tax_group_id.name
                            == "Otros Impuestos"
                        ).mapped("amount_currency")
                    )
                )

                # Monto Propina Legal
                inv.legal_tip = inv._convert_to_local_currency(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.tax_line_id.tax_group_id.name == "Propina"
                        ).mapped("amount_currency")
                    )
                )

                # ITBIS sujeto a proporcionalidad
                inv.proportionality_tax = inv._convert_to_local_currency(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.account_id.account_fiscal_type
                            in ["A29", "A30"]
                        ).mapped("amount_currency")
                    )
                )

                # ITBIS llevado al Costo
                inv.cost_itbis = inv._convert_to_local_currency(
                    sum(
                        tax_line_ids.filtered(
                            lambda tax: tax.account_id.account_fiscal_type == "A51"
                        ).mapped("amount_currency")
                    )
                )

    @api.depends("invoice_line_ids", "invoice_line_ids.product_id", "state", "payment_state")
    def _compute_amount_fields(self):
        """Compute Purchase amount by product type"""
        for inv in self:
            if inv.move_type in ["in_invoice", "in_refund"] and inv.state != "draft":
                service_amount = 0
                good_amount = 0

                for line in inv.invoice_line_ids:

                    # Monto calculado en bienes
                    if line.product_id.type in ["product", "consu"]:
                        good_amount += line.price_subtotal

                    # Si la linea no tiene un producto, o el producto es de tipo Servicio
                    elif not line.product_id or line.product_id.type in ["service"]:
                        service_amount += line.price_subtotal
                        continue

                    # Monto calculado en servicio
                    else:
                        service_amount += line.price_subtotal

                inv.service_total_amount = inv._convert_to_local_currency(service_amount)
                inv.good_total_amount = inv._convert_to_local_currency(good_amount)

    
    @api.depends("line_ids", "state", "move_type", "payment_state")
    def _compute_isr_withholding_type(self):
        """Compute ISR Withholding Type
        Keyword / Values:
        01 -- Alquileres
        02 -- Honorarios por Servicios
        03 -- Otras Rentas
        04 -- Rentas Presuntas
        05 -- Intereses Pagados a Personas Jurídicas
        06 -- Intereses Pagados a Personas Físicas
        07 -- Retención por Proveedores del Estado
        08 -- Juegos Telefónicos
        """

        for inv in self.filtered(
            lambda i: i.move_type == "in_invoice" and i.payment_state == "paid"
        ):

            # Solo me interesa los lines que son de tipo Impuesto ISR
            tax_line_id = inv.line_ids.filtered(
                lambda t: t.tax_line_id.purchase_tax_type == "isr"
            )
            if tax_line_id:  # invoice tax lines use case
                inv.isr_withholding_type = tax_line_id[0].tax_line_id.isr_retention_type
            else:  # in payment/journal entry use case
                aml_ids = (
                    self.env["account.move"]
                    .browse(p["move_id"] for p in inv._get_invoice_payment_widget())
                    .mapped("line_ids")
                    .filtered(lambda aml: aml.account_id.isr_retention_type)
                )
                if aml_ids:
                    inv.isr_withholding_type = aml_ids[0].account_id.isr_retention_type

    def _get_payment_string(self):
        """Compute Vendor Bills payment method string

        Keyword / Values:
        cash        -- Efectivo
        bank        -- Cheques / Transferencias / Depósitos
        card        -- Tarjeta Crédito / Débito
        credit      -- Compra a Crédito
        swap        -- Permuta
        credit_note -- Notas de Crédito
        mixed       -- Mixto
        """
        payments = []
        p_string = ""

        for payment in self._get_invoice_payment_widget():
            payment_id = self.env["account.payment"].browse(
                payment.get("account_payment_id")
            )
            move_id = False
            if payment_id:
                if payment_id.journal_id.type in ["cash", "bank"]:
                    p_string = payment_id.journal_id.l10n_do_payment_form

            if not payment_id:
                move_id = self.env["account.move"].browse(payment.get("move_id"))
                if move_id:
                    p_string = "swap"

            # If invoice is paid, but the payment doesn't come from
            # a journal, assume it is a credit note
            payment = p_string if payment_id or move_id else "credit_note"
            payments.append(payment)

        methods = {p for p in payments}
        if len(methods) == 1:
            return list(methods)[0]
        elif len(methods) > 1:
            return "mixed"

    @api.depends("payment_state")
    def _compute_in_invoice_payment_form(self):
        for inv in self:
            if inv.payment_state == "paid":
                payment_dict = {
                    "cash": "01",
                    "bank": "02",
                    "card": "03",
                    "credit": "04",
                    "swap": "05",
                    "credit_note": "06",
                    "mixed": "07",
                }
                inv.payment_form = payment_dict.get(inv._get_payment_string())
            else:
                inv.payment_form = "04"

    @api.depends("line_ids", "state")
    def _compute_invoiced_itbis(self):
        """Compute invoice invoiced_itbis taking into account the currency"""
        for inv in self:
            if inv.state != "draft":
                amount = 0
                itbis_taxes = ["ITBIS", "ITBIS 18%"]

                # Solo me interesa los lines que son de tipo Impuesto.
                tax_line_ids = inv.line_ids.filtered(
                                lambda tax: bool(tax.tax_line_id)
                                )

                for tax in tax_line_ids:
                    if (
                        tax.tax_line_id.tax_group_id.name in itbis_taxes
                        and tax.tax_line_id.purchase_tax_type != "ritbis"
                    ):
                        amount += tax.amount_currency
                    inv.invoiced_itbis = inv._convert_to_local_currency(amount)

    def _get_payment_move_iterator(self, payment, inv_type, witheld_type):
        payment_id = self.env["account.payment"].browse(
            payment.get("account_payment_id")
        )
        if payment_id:
            if inv_type == "out_invoice":
                return [
                    move_line.debit
                    for move_line in payment_id.move_line_ids
                    if move_line.account_id.account_fiscal_type in witheld_type
                ]
            else:
                return [
                    move_line.credit
                    for move_line in payment_id.move_line_ids
                    if move_line.account_id.account_fiscal_type in witheld_type
                ]
        else:
            move_id = self.env["account.move"].browse(payment.get("move_id"))
            if move_id:
                if inv_type == "out_invoice":
                    return [
                        move_line.debit
                        for move_line in move_id.line_ids
                        if move_line.account_id.account_fiscal_type in witheld_type
                    ]
                else:
                    return [
                        move_line.credit
                        for move_line in move_id.line_ids
                        if move_line.account_id.account_fiscal_type in witheld_type
                    ]

    def compute_witheld_taxes(self):
        self._compute_withheld_taxes()

    @api.depends("payment_state", "move_type")
    def _compute_withheld_taxes(self):
        for inv in self:
            if inv.payment_state == "paid":
                inv.third_withheld_itbis = 0
                inv.third_income_withholding = 0
                withholding_amounts_dict = {"A34": 0, "A36": 0, "ISR": 0, "A38": 0}

                if inv.move_type == "in_invoice":
                    # Solo me interesa los lines que son de tipo Impuesto.
                    tax_line_ids = inv.line_ids.filtered(
                                lambda tax: bool(tax.tax_line_id)
                                )

                    # Monto ITBIS Retenido por impuesto
                    inv.withholded_itbis = abs(
                        inv._convert_to_local_currency(
                            sum(
                                tax_line_ids.filtered(
                                    lambda tax: tax.tax_line_id.purchase_tax_type == "ritbis"
                                ).mapped("amount_currency")
                            )
                        )
                    )
                    
                    # Monto Retención Renta por impuesto
                    inv.income_withholding = abs(
                        inv._convert_to_local_currency(
                            sum(
                                tax_line_ids.filtered(
                                    lambda tax: tax.tax_line_id.purchase_tax_type == "isr"
                                ).mapped("amount_currency")
                            )
                        )
                    )

                move_ids = [p["move_id"] for p in inv._get_invoice_payment_widget()]

                aml_ids = (
                    self.env["account.move"]
                    .browse(move_ids)
                    .mapped("line_ids")
                    .filtered(lambda aml: bool(aml.journal_id.default_account_id.account_fiscal_type))
                )

                if aml_ids:
                    for aml in aml_ids:
                        fiscal_type = aml.journal_id.default_account_id.account_fiscal_type
                        if fiscal_type in withholding_amounts_dict:
                            withholding_amounts_dict[fiscal_type] += (
                                aml.debit if inv.move_type == "out_invoice" else aml.credit
                            )

                    withheld_itbis = sum(
                        v
                        for k, v in withholding_amounts_dict.items()
                        if k in ("A34", "A36")
                    )
                    withheld_isr = sum(
                        v
                        for k, v in withholding_amounts_dict.items()
                        if k in ("ISR", "A38")
                    )

                    if inv.move_type == "out_invoice":
                        inv.third_withheld_itbis = withheld_itbis
                        inv.third_income_withholding = withheld_isr

                    elif inv.move_type == "in_invoice":
                        inv.withholded_itbis = withheld_itbis
                        inv.income_withholding = withheld_isr

                if any([inv.third_withheld_itbis, inv.third_income_withholding]):
                            inv._compute_invoice_payment_date()
                
                if any([inv.withholded_itbis, inv.income_withholding]):
                            inv._compute_invoice_payment_date()

    @api.depends("invoiced_itbis", "cost_itbis", "state")
    def _compute_advance_itbis(self):
        for inv in self:
            if inv.state != "draft":
                inv.advance_itbis = inv.invoiced_itbis - inv.cost_itbis

    # VER SI ESTO FUNCIONA BIEN Y REALMENTE LA MARCA COMO IS_EXTERIOR
    @api.depends("l10n_latam_document_type_id")
    def _compute_is_exterior(self):
        for inv in self:
            inv.is_exterior = (
                True if inv.l10n_latam_document_type_id.l10n_do_ncf_type == "exterior" else False
            )

    # VER SI ESTO QUEDA BIEN Y EL SELF DEVUELVE UN CODIGO EN LUGAR DE UN TEXTO
    @api.onchange("l10n_do_expense_type")
    def onchange_l10n_do_expense_type(self):
        self.service_type_detail = False
        return {
            "domain": {"service_type_detail": [("parent_code", "=", self.l10n_do_expense_type)]}
        }

    @api.onchange("journal_id")
    def ext_onchange_journal_id(self):
        self.service_type_detail = False

    # ISR Percibido       --> Este campo se va con 12 espacios en 0 para el 606
    # ITBIS Percibido     --> Este campo se va con 12 espacios en 0 para el 606
    payment_date = fields.Date(compute="_compute_taxes_fields", store=True)
    service_total_amount = fields.Monetary(
        compute="_compute_amount_fields",
        store=True,
        currency_field="company_currency_id",
    )
    good_total_amount = fields.Monetary(
        compute="_compute_amount_fields",
        store=True,
        currency_field="company_currency_id",
    )
    invoiced_itbis = fields.Monetary(
        compute="_compute_invoiced_itbis",
        store=True,
        currency_field="company_currency_id",
    )
    withholded_itbis = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    proportionality_tax = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    cost_itbis = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    advance_itbis = fields.Monetary(
        compute="_compute_advance_itbis",
        store=True,
        currency_field="company_currency_id",
    )
    isr_withholding_type = fields.Char(
        compute="_compute_isr_withholding_type", store=True, size=2
    )
    income_withholding = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    selective_tax = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    other_taxes = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    legal_tip = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    payment_form = fields.Selection(
        [
            ("01", "Cash"),
            ("02", "Check / Transfer / Deposit"),
            ("03", "Credit Card / Debit Card"),
            ("04", "Credit"),
            ("05", "Swap"),
            ("06", "Credit Note"),
            ("07", "Mixed"),
        ],
        compute="_compute_in_invoice_payment_form",
        store=True,
    )
    third_withheld_itbis = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    third_income_withholding = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    is_exterior = fields.Boolean(compute="_compute_is_exterior", store=True)
    
    service_type_detail = fields.Many2one("invoice.service.type.detail")
    fiscal_status = fields.Selection(
        [("normal", "Partial"), ("done", "Reported"), ("blocked", "Not Sent")],
        copy=False,
        help="* The 'Grey' status means invoice isn't fully reported and may appear "
        "in other report if a withholding is applied.\n"
        "* The 'Green' status means invoice is fully reported.\n"
        "* The 'Red' status means invoice is included in a non sent DGII report.\n"
        "* The blank status means that the invoice have"
        "not been included in a report.",
    )
    
   
    @api.model
    def norma_recompute(self,records=None):
        """
        This method add all compute fields into []env
        add_todo and then recompute
        all compute fields in case dgii config change and need to recompute.
        :return:
        """
        if records:
            invoice_ids = records
        else:
            invoice_ids = self.search([('id','=',self.id)])
        invoice_qty = len(invoice_ids) 
        _logger.warning(f"Inicio: Recalculando Campos de {invoice_qty} Factura(s)")

        for k, v in self.fields_get().items():
            if v.get("store") and v.get("depends"):
                _logger.warning(f"=====> Recalculando Campo {k}")
                self.env.add_to_compute(self._fields[k], invoice_ids) 
        _logger.warning(f"Finalizado: Recalculando Campos de {invoice_qty} Factura(s)")
