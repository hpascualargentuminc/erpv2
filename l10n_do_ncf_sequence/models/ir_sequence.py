from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class IrSequence(models.Model):
    _inherit = "ir.sequence"

    @api.model
    def next_by_code_active(self, sequence_code, sequence_date, check_active):
        
        self.check_access_rights('read')
        company_id = self.env.company.id
        seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [company_id, False])], order='company_id')
        if not seq_ids:
            _logger.debug("No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current company." % sequence_code)
            return False
        seq_id = seq_ids[0]
        _logger.info('Ir_Sequence: sequence_code: %s | sequence_id: %s | code: %s | name: %s', sequence_code, seq_id.id, seq_id.code, seq_id.name)
        return seq_id._next_active(sequence_date=sequence_date, check_active=check_active)

    def _next_active(self, sequence_date, check_active):
        if not self.use_date_range:
            return self._next_do()
        # date mode
        dt = sequence_date or self._context.get('ir_sequence_date', fields.Date.today())
        seq_date = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt), ('active', '=', check_active)], limit=1)
        if not seq_date:
            return 'N/A'
        if seq_date.number_next_actual > seq_date.max_number_next:
            return 'R/N/A'
        valor = seq_date.with_context(ir_sequence_date_range=seq_date.date_from)._next()
        _logger.info('Ir_Sequence: sequence_date: %s | valor: %s', sequence_date, valor)
        return valor