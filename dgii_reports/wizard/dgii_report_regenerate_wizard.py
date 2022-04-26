from odoo import models, fields, api


class DgiiReportRegenerateWizard(models.TransientModel):
    """
    This wizard only objective is to show a warning when a dgii report
    is about to be regenerated.
    """

    _name = "dgii.report.regenerate.wizard"
    _description = "DGII Report Regenerate Wizard"

    report_id = fields.Many2one("dgii.reports", "Report")

    def regenerate(self):
        self.report_id._generate_report()
