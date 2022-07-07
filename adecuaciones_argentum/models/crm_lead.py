from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"
    
    first_invoice_date = fields.Date(string="Fecha de la 1ra Factura")
    first_invoice_amount = fields.Monetary(string="Total de la 1ra Factura", currency_field='company_currency')
    
    @api.onchange('date_deadline')
    def _update_data_on_opportunity(self):
        for opt in self:
            _logger.info(f"Order IDs: {self.order_ids}")
            for order in opt.order_ids:
                _logger.info(f"Order state: {order.state}")
                _logger.info(f"Opp Datedeadline: {opt.date_deadline}")
                _logger.info(f"Order Payment Term: {order.payment_term_id}")
                if order.state not in ('cancel') and opt.date_deadline and order.payment_term_id:
                    fid = order.payment_term_id.compute(value=order.base_amount_untaxed, date_ref=opt.date_deadline)[0][0]
                    fia = opt.expected_revenue * (order.first_invoice_perc/100)
                    _logger.info(f"first_invoice_date: {fid} | first_invoice_amount: {fia}")
                    opt.first_invoice_date = fid
                    opt.first_invoice_amount = fia
                    _logger.info(f"UPD: first_invoice_date: {opt.first_invoice_date} | first_invoice_amount: {opt.first_invoice_amount}")
                    #opp.sudo().write({'first_invoice_date': first_invoice_date, 'first_invoice_amount': first_invoice_amount})
                    # break
            