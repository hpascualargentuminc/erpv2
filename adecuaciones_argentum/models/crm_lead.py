from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"
    
    first_invoice_date = fields.Date(string="Fecha de la 1ra Factura")
    first_invoice_amount = fields.Monetary(string="Total de la 1ra Factura", currency_field='company_currency')
    
    @api.onchange('date_deadline','expected_revenue')
    def _update_data_opportunity(self):
        for record in self:
            invoice_date = record.first_invoice_date
            invoice_amount = record.first_invoice_amount
            for order in record.order_ids:
                if order.state not in ('cancel') and record.date_deadline and order.payment_term_id:
                    invoice_date = order.payment_term_id.compute(value=order.base_amount_untaxed, date_ref=record.date_deadline)[0][0]
                    invoice_amount = record.expected_revenue * (order.first_invoice_perc/100)
        
            record.first_invoice_date = invoice_date
            record.first_invoice_amount = invoice_amount     