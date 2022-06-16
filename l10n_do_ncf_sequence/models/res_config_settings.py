from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_invoice_with_different_date = fields.Boolean(string="Permitir que las facturas se generen con fecha distinta a la actual", default=False)

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('account.allow_invoice_with_different_date',
                                                         self.allow_invoice_with_different_date)
        res = super(ResConfigSettings, self).set_values()
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        allow_invoice_not_today = self.env['ir.config_parameter'].sudo().get_param(
            'account.allow_invoice_with_different_date',
            self.allow_invoice_with_different_date)
        res.update(
            allow_invoice_with_different_date = allow_invoice_not_today
        )
        return res
