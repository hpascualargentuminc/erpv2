# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    rrhh_notes = fields.Text(string='Notas RRHH')