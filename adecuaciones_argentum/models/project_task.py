# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, models, fields


class Task(models.Model):
    _inherit = 'project.task'

    invoice_id = fields.Many2one('account.move', string='Factura', help='Factura asociada a la Tarea/Hito')
    parent_partner_id = fields.Many2one('res.partner', compute="_compute_parent_partner_id")
    
    @api.onchange('partner_id')
    def _compute_parent_partner_id(self):
        if self.partner_id:
            self.parent_partner_id = self.partner_id
            if self.partner_id.parent_id != False:
                self.parent_partner_id = self.partner_id.parent_id
                
