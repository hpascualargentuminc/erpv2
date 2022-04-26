# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from os import path
from csv import reader
from io import StringIO
from datetime import date
from datetime import datetime
import itertools
from odoo import _, api, models
from odoo.exceptions import UserError


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _check_txt(self, filename):
        return filename and filename.lower().strip().endswith('.csv')
    
    def _parse_file(self, data_file):
        if len(self.attachment_ids) > 1:
            txt = [bool(self._check_txt(att.name)) for att in self.attachment_ids]
            if True in txt and False in txt:
                raise UserError(_('Mezclar archivos TXT con otros formatos de archivos no está permitido.'))
            if txt.count(True) > 1:
                raise UserError(_('Solo un archivo TXT puede ser seleccionado.'))
            return super(AccountBankStatementImport, self).import_file()

        if not self._check_txt(self.attachment_ids.name):
            return super(AccountBankStatementImport, self)._parse_file(data_file)

        # Obtengo el Diario y sus datos
        journal = self.env['account.journal'].browse(self.env.context.get('journal_id'))
        currency_code = (journal.currency_id or journal.company_id.currency_id).name
        currency_symbol = (journal.currency_id or journal.company_id.currency_id).symbol
        account_number = journal.bank_account_id.acc_number
        
        name = _('%s: %s') % (
            journal.code,
            path.basename(self.attachment_ids.name),
        )
        
        statement_name = "BHD "+ str(date.today().strftime("%Y-%m-%d")) + " Bank Statement"
        
        lines = self._parse_lines(data_file, currency_code, currency_symbol)
        if not lines:
            return currency_code, account_number, [{
                'name': statement_name,
                'transactions': [],
            }]
        
        lines = list(sorted(
            lines,
            key=lambda line: line['timestamp']
        ))
        
        first_line = lines[0]
        last_line = lines[-1]
        data = {
            'name': statement_name,
            #'date': first_line['timestamp'],
        }
        
        transactions = list(itertools.chain.from_iterable(map(
            lambda line: self._convert_line_to_transactions(line),
            lines
        )))
        data.update({
            'transactions': transactions,
        })
        
        return currency_code, account_number, [data]
        
    def _parse_lines(self, data_file, currency_code, currency_symbol):
        csv_options = {}
        csv_options['delimiter'] = ','
        csv_options['quotechar'] = '"'
        csv = reader(
            StringIO(data_file.decode('latin-1')),
            **csv_options
        )

        header = [value.strip() for value in next(csv)]
        
        timestamp_column = header.index('Fecha')
        transaction_id_column = header.index('Referencia')
        description_column = header.index('Detalle de Transacciones')
        debit_column = header.index('Débitos')
        credit_column = header.index('Créditos')
        balance_column = header.index('Balance')
        
        rows = csv

        lines = []
        for row in rows:
            values = list(row)
            try:
                date_format = "%d/%m/%Y"
                timestamp = datetime.strptime(values[timestamp_column], date_format)
                
                credit = values[credit_column]
                debit = values[debit_column]
                balance = values[balance_column]
                
                if credit:
                    credit = credit.replace(currency_symbol,'')
                    amount = str(credit.replace(',',''))
                elif debit:
                    debit = values[debit_column].replace(currency_symbol,'')
                    amount = "-"+str(str(debit.replace(',','')).replace(' ',''))
                
                transaction_id = values[transaction_id_column]
                description = values[description_column]

                line = {
                    'timestamp': timestamp,
                    'amount': amount,
                    'transaction_id': transaction_id,
                    'description': description,
                    'balance': balance
                }
            
                lines.append(line)
            except:
                pass
        return lines

    @api.model
    def _convert_line_to_transactions(self, line):
        timestamp = line.get('timestamp')
        amount = line.get('amount')
        transaction_id = line.get('transaction_id')
        description = line.get('description')
        balance = line.get('balance')

        transaction = {
            'date': str(timestamp),
            'amount': str(amount),
            'ref': str(transaction_id)
        }
        
        transaction['unique_import_id'] = 'BHD|%s|%s|%s|%s|%s' % (
            timestamp,
            amount,
            description,
            transaction_id,
            balance
        )

        transaction['payment_ref'] = description or _('N/A')

        return [transaction]