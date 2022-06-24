# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    base_amount_untaxed = fields.Monetary(string="Monto Base", store=True, compute='_update_base_amount_untaxed')
    company_currency_id = fields.Many2one(related='company_id.currency_id', depends=['company_id.currency_id'], store=True, string='Moneda de la Empresa')
    partner_purchase_order = fields.Char(string="O/C Cliente")
    first_invoice_perc = fields.Float(string="Porc. 1ra Factura", default=100.00)
    
    @api.onchange('first_invoice_perc','state','payment_term_id')
    def _update_data_on_opportunity(self):
        for order in self:
            if order.opportunity_id and order.payment_term_id:
                first_invoice_date = order.payment_term_id.compute(value=order.base_amount_untaxed, date_ref=order.opportunity_id.date_deadline)[0][0]
                first_invoice_amount = order.opportunity_id.expected_revenue * (order.first_invoice_perc/100)
                order.opportunity_id.sudo().write({'first_invoice_date': first_invoice_date, 'first_invoice_amount': first_invoice_amount})
            
    @api.depends('order_line.price_total')
    def _update_base_amount_untaxed(self):
        for order in self:
            base_amount_untaxed = total_amount_untaxed = 0.0
            for line in order.order_line:
                total_amount_untaxed += line.price_subtotal
            base_amount_untaxed = total_amount_untaxed / order.currency_rate
            order.update({'base_amount_untaxed': base_amount_untaxed,})
            if order.opportunity_id:
                order.opportunity_id.update({'expected_revenue': base_amount_untaxed,})

    def action_preview_lead(self):
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_opportunities")
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_id': self.opportunity_id.id
        }
        action['domain'] = [('id', '=', self.opportunity_id.id)]
        if self.opportunity_id:
            action['views'] = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
            action['res_id'] = self.opportunity_id.id
        return action
    
    def _prepare_invoice(self):
        # Este método se llama dentro de la acción de creación de Factura desde la SO
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        # Seteamos los campos custom de Argentum SO que deben viajar a la Factura
        if self.partner_purchase_order:
            invoice_vals['partner_purchase_order'] = self.partner_purchase_order
        return invoice_vals