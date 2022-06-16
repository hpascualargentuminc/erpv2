import re
import logging
from psycopg2 import sql
from werkzeug import urls
from datetime import date, datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError

_logger = logging.getLogger(__name__)
class AccountMove(models.Model):
    _inherit = "account.move"

    sequence_almost_depleted = fields.Boolean(compute="_compute_sequence_almost_depleted")

    def _set_next_sequence(self):
        self.ensure_one()

        if not self._context.get("is_l10n_do_seq", False):
            return super(AccountMove, self)._set_next_sequence()

        seq_code = self.l10n_latam_document_type_id.sequence_id.code
        sequence_date = self._context.get('ir_sequence_date', fields.Date.today())
            
        # No deseamos que genere NCF si el Diario no es Fiscal, y la factura está en estado DRAFT o CANCEL
        # Tampoco si los campos donde va el NCF ya están populados (por ejemplo, para facturas fiscales de Proveedores)
        if self.journal_id.l10n_latam_use_documents \
            and not self.l10n_latam_document_number \
            and not self.l10n_do_fiscal_number \
            and not self[self._l10n_do_sequence_field] \
            and self.state not in ["draft","cancel"]:

            ncf = self.env['ir.sequence'].next_by_code_active(sequence_code=seq_code, sequence_date=sequence_date, check_active=True)

            _logger.info('Account_Move: NCF generado: %s', ncf)
            # Si luego de lo anterior esto sale en blanco, es que no hay secuencia disponible
            if ncf=='N/A':
                raise ValidationError(
                        _("Atención. No se ha encontrado rango de NCF activo para ({}) {}. Consulte con su área de Administración.").format(
                            self.l10n_latam_document_type_id.code,
                            self.l10n_latam_document_type_id.name
                        ))
            elif ncf=='R/N/A':
                raise ValidationError(
                        _("Atención. Se acaba de agotar la secuencia de NCF para ({}) {}. Consulte con su área de Administración.").format(
                            self.l10n_latam_document_type_id.code,
                            self.l10n_latam_document_type_id.name
                        ))
            else:
                self[
                    self._l10n_do_sequence_field
                ] = ncf
                _logger.info('Account_Move: NCF %s asignado a factura %s del cliente/proveedor %s', ncf, self.name, self.partner_id.name)

    def _post(self, soft=True):
        for inv in self:
            allow_invoice_with_different_date = self.env['ir.config_parameter'].sudo().get_param('account.allow_invoice_with_different_date')
            seq_code = inv.l10n_latam_document_type_id.sequence_id.code
            
            # Para aplicar el control de fecha, debemos validar que sea un comprobante que se genera en nuestra empresa
            if (inv.move_type in ('out_refund', 'out_invoice')\
                or (inv.move_type in ('in_invoice') and seq_code in ('B11','B13') )):
                
                is_invoice_date_different_from_today = inv.invoice_date!=False and inv.invoice_date!=date.today()

                if not allow_invoice_with_different_date and is_invoice_date_different_from_today:
                    raise ValidationError(
                                _(f"Atención. No se puede Confirmar la factura porque la fecha de ésta, {inv.invoice_date}, es diferente a la fecha actual. Corrija o borre la fecha, para poder Confirmar esta factura."))
                

            
            if (
                # Hay que ponerlo negativo, porque en una parte de account_move le aplican un signo al revés
                inv.amount_untaxed_signed <= -250000
                and inv.l10n_latam_document_type_id.l10n_do_ncf_type != "unique"
                and not inv.partner_id.vat
            ):
                raise ValidationError(
                    _(
                        "Para poder emitir una Factura con monto igual o mayor a "
                        " RD$250,000 se requiere que el "
                        " cliente tenga RNC o Cédula."
                    )
                )

            if (
                inv.l10n_latam_document_type_id.l10n_do_ncf_type == "exterior"
                and inv.partner_id.country_id.code == "DO"
            ):
                raise ValidationError(
                    _(
                        u"Para Remesas al Exterior el Proveedor debe"
                        u" tener país diferente a República Dominicana"
                    )
                )

            if (
                inv.move_type == "out_refund"
                and inv.journal_id.l10n_latam_use_documents
                and inv.amount_untaxed_signed <= -250000
                and not inv.partner_id.vat
            ):
                raise ValidationError(
                    _(
                        "Para poder emitir una Nota de Crédito con monto igual o mayor a "
                        " RD$250,000 se requiere que el "
                        " cliente tenga RNC o Cédula."
                    )
                )

        res = super()._post(soft)

        l10n_do_invoices = self.filtered(
            lambda inv: inv.company_id.country_id == self.env.ref("base.do")
            and inv.l10n_latam_use_documents
        )

        for invoice in l10n_do_invoices.filtered(
            lambda inv: inv.l10n_latam_document_type_id
        ):
            invoice.l10n_do_ncf_expiration_date = self.get_ncf_expiration_date()

        non_payer_type_invoices = l10n_do_invoices.filtered(
            lambda inv: not inv.partner_id.l10n_do_dgii_tax_payer_type
        )
        if non_payer_type_invoices: 
            raise ValidationError(_("Las facturas fiscales requieren que el cliente tenga un Tipo de Contribuyente."))

        return res
    
    def get_ncf_expiration_date(self):
        for inv in self:
            if inv.state != "draft" and inv.journal_id.l10n_latam_use_documents and not inv.l10n_latam_manual_document_number:
                if inv.l10n_latam_document_type_id:
                    try:
                        dt = self._context.get('ir_sequence_date', fields.Date.today())
                        seq_date = self.env["ir.sequence.date_range"].search(
                            [
                                ("sequence_id", "=", inv.l10n_latam_document_type_id.sequence_id.id),
                                ("date_from", "<=", dt),
                                ("date_to", ">=", dt),
                            ],
                            limit=1,
                            )
                        
                        ncf_expiration_date = [
                            dr.date_to
                            for dr in seq_date
                        ][0]

                        return ncf_expiration_date

                    except IndexError:
                        raise ValidationError(
                            _("Atención. No se ha encontrado rango de NCF activo para ({}) {}. Consulte con su área de Administración.").format(
                                self.l10n_latam_document_type_id.code,
                                self.l10n_latam_document_type_id.name
                            ))
    
    def _compute_l10n_do_enable_first_sequence(self):
        # Es necesario para que no pida que el primer NCF de un tipo se tenga que poner a mano
        self.l10n_do_enable_first_sequence = False
    
    @api.depends("journal_id", "l10n_latam_document_type_id")
    def _compute_sequence_almost_depleted(self):
        self.sequence_almost_depleted = False
        # DE MOMENTO SE COMENTA ESTE MÉTODO, PARA VER SI ES EL QUE PROVOCA LOS SALTOS DE NCF
        # for invoice in self:
        #     if (
        #         invoice.journal_id.l10n_latam_use_documents
        #         and invoice.l10n_latam_document_type_id
        #         and not invoice.l10n_latam_manual_document_number
        #         and invoice.state == "draft"
        #     ):
        #         dt = self._context.get('ir_sequence_date', fields.Date.today())
        #         sequence = self.env['ir.sequence.date_range'].search([('sequence_id', '=', invoice.l10n_latam_document_type_id.sequence_id.id), ('date_from', '<=', dt), ('date_to', '>=', dt), ('active', '=', True)], limit=1)
                
        #         if sequence:
        #             if sequence.number_next_actual >= sequence.warning_ncf:
        #                 invoice.sequence_almost_depleted = True
    
    @api.constrains("state", "tax_ids")
    def validate_special_exempt(self):
        """Validates an invoice with Regímenes Especiales sale_fiscal_type
        does not contain nor ITBIS or ISC.

        See DGII Norma 05-19, Art 3 for further information.
        """
        for inv in self:
            if (
                inv.move_type == "out_invoice"
                and inv.state in ("draft", "cancel")
                and inv.l10n_latam_document_type_id.l10n_do_ncf_type == "special"
            ):

                # If any invoice tax in ITBIS or ISC
                if any(
                    [
                        tax
                        for tax in inv.invoice_line_ids.tax_ids.filtered(
                            lambda tax: tax.tax_group_id.name in ("ITBIS", "ISC")
                            and tax.amount != 0
                        )
                    ]
                ):
                    raise UserError(
                        _(
                            "No puede crear una factura para Régimen Especial "
                            " con ITBIS/ISC.\n\n"
                            "Consulte la Norma General 05-19, Art. 3 de la DGII"
                        )
                    )
    
    @api.constrains("state", "tax_ids")
    def validate_informal_withholding(self):
        """Validates an invoice with Comprobante de Compras has 100% ITBIS
        withholding.

        See DGII Norma 05-19, Art 7 for further information.
        """

        for inv in self:
            if (
                inv.move_type == "in_invoice"
                and inv.state in ("draft")
                and inv.l10n_latam_document_type_id.l10n_do_ncf_type == "informal"
            ):

                # If the sum of all taxes of category ITBIS is not 0
                if sum(
                    [
                        tax.amount
                        for tax in inv.invoice_line_ids.tax_ids.filtered(
                            lambda tax: tax.tax_group_id.name in ["ITBIS", "R-ITBIS"]
                        )
                    ]
                ):
                    raise UserError(
                        _(
                            "Debe retener el 100% del ITBIS en esta Factura.\n\n"
                            "Consulte la Norma General 05-19, Art. 7 de la DGII"
                        )
                    )

    # @api.onchange("l10n_latam_document_number")
    # def onchange_ncf(self):
    #     if self.journal_id.type == "purchase" and self.journal_id.l10n_latam_use_documents:
    #         self.validate_fiscal_purchase()
    
    # def validate_fiscal_purchase(self):
    #     NCF = self.l10n_latam_document_number if self.l10n_latam_document_number else None
        #if NCF:

            # el día que se implemente el API para validar NCF, usaremos esto
            # if (
            #     self.journal_id.ncf_remote_validation
            #     and len(NCF) == 11
            #     and not ncf_validation.check_dgii(self.partner_id.vat, NCF)
            # ):
            #     raise ValidationError(
            #         _(
            #             u"NCF NO pasó validación en DGII\n\n"
            #             u"¡El número de comprobante *{}* del proveedor "
            #             u"*{}* no pasó la validación en "
            #             "DGII! Verifique que el NCF y el RNC del "
            #             u"proveedor estén correctamente "
            #             u"digitados, o si los números de ese NCF se "
            #             "le agotaron al proveedor"
            #         ).format(NCF, self.partner_id.name)
            #     )
