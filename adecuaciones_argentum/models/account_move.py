# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"
    
    partner_purchase_order = fields.Char(string="O/C Cliente", store=True)
    generate_on = fields.Datetime(string="Fecha para Generarla", store=True)
    
    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.country_code == "DO":
            return "adecuaciones_argentum.report_invoice_document_inherited_argentum"
        return super()._get_name_invoice_report()