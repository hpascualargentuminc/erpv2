from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"
    
    first_invoice_date = fields.Date(string="Fecha de la 1ra Factura")
    first_invoice_amount = fields.Monetary(string="Total de la 1ra Factura", currency_field='company_currency')
    
    @api.onchange('date_deadline','expected_revenue')
    def _update_data_on_opportunity(self):
        for opp in self:
            for order in opp.order_ids:
                if order.state not in ('cancel') and opp.date_deadline and order.payment_term_id:
                    first_invoice_date = order.payment_term_id.compute(value=order.base_amount_untaxed, date_ref=opp.date_deadline)[0][0]
                    first_invoice_amount = opp.expected_revenue * (order.first_invoice_perc/100)
                    opp.sudo().write({'first_invoice_date': first_invoice_date, 'first_invoice_amount': first_invoice_amount})
                    break
            