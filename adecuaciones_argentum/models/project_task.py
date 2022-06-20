# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, models, fields


class Task(models.Model):
    _inherit = 'project.task'

    invoice_id = fields.Many2one('account.move', string='Factura', help='Factura asociada a la Tarea/Hito')
    parent_partner_id = fields.Many2one('res.partner', compute="_compute_parent_partner_id", store=True)
    
    @api.onchange('partner_id')
    def _compute_parent_partner_id(self):
        for record in self:    
            if record.partner_id.company_type == 'company':
                record.parent_partner_id = record.partner_id
            elif record.partner_id.company_type == 'person':
                record.parent_partner_id = record.partner_id.parent_id if record.partner_id.parent_id else record.partner_id
                
