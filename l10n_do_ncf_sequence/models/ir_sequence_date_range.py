from odoo import models, fields, api

class IrSequenceDateRange(models.Model):
    _inherit = "ir.sequence.date_range"

    max_number_next = fields.Integer(u"Número Máximo", default=100)

    warning_ncf = fields.Integer(string="NCF de Alerta")

    active = fields.Boolean(string="Secuencia Activa", default=True)
