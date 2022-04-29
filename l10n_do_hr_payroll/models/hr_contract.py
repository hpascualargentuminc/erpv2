# -*- coding:utf-8 -*-

from odoo import  fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'
    base_hour_price = fields.Monetary("Valor hora")
    day_level1_extra_hour_price  = fields.Monetary("Valor hora extra nivel 1")
    day_level2_extra_hour_price  = fields.Monetary("Valor hora extra nivel 2")
    night_extra_hour_price  = fields.Monetary("Valor hora extra noctura")
