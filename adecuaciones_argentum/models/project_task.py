# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, models, fields


class Task(models.Model):
    _inherit = 'project.task'

    invoice_id = fields.Many2one('account.move', string='Factura', help='Factura asociada a la Tarea/Hito')
