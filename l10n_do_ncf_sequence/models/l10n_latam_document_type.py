# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class L10nLatamDocumentType(models.Model):
    _inherit = "l10n_latam.document.type"
    
    sequence_id = fields.Many2one('ir.sequence', string='Secuencia de NCF', required=False, copy=False)

    date_range_ids = fields.One2many(related="sequence_id.date_range_ids", string='Rangos de NCF', readonly=False)
