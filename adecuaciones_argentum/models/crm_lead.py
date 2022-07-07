from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"
    
    first_invoice_date = fields.Date(string="Fecha de la 1ra Factura")
    first_invoice_amount = fields.Monetary(string="Total de la 1ra Factura", currency_field='company_currency')
    
    @api.onchange('date_deadline')
    def _update_data_opportunity(self):
        for record in self:
            fid = record.first_invoice_date
            fia = record.first_invoice_amount
            _logger.info(f"Order IDs: {self.order_ids}")
            for order in opt.order_ids:
                _logger.info(f"Order state: {order.state}")
                _logger.info(f"Opp Datedeadline: {record.date_deadline}")
                _logger.info(f"Order Payment Term: {order.payment_term_id}")
                if order.state not in ('cancel') and record.date_deadline and order.payment_term_id:
                    fid = order.payment_term_id.compute(value=order.base_amount_untaxed, date_ref=record.date_deadline)[0][0]
                    fia = record.expected_revenue * (order.first_invoice_perc/100)
                    _logger.info(f"first_invoice_date: {fid} | first_invoice_amount: {fia}")
        
            record.first_invoice_date = fid
            record.first_invoice_amount = fia
            _logger.info(f"UPD: first_invoice_date: {fid} | first_invoice_amount: {fia}")
            _logger.info(f"UPD 2: first_invoice_date: {record.first_invoice_date} | first_invoice_amount: {record.first_invoice_amount}")
            #record.sudo().update({'first_invoice_date': fid, 'first_invoice_amount': fia})
            # break
            