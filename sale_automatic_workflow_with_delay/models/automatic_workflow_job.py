# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AutomaticWorkflowJob(models.Model):
    _inherit = "automatic.workflow.job"

    def run_with_workflow(self, sale_workflow):
        if sale_workflow.validate_order_with_delay:
            self.env = self.env(
                context=dict(self.env.context, sale_workflow_validate_with_delay=True)
            )
        return super(AutomaticWorkflowJob, self).run_with_workflow(sale_workflow)

    def _validate_sale_orders(self, order_filter):
        if self.env.context.get("sale_workflow_validate_with_delay"):
            if not self.env.context.get("sale_workflow_job_delayed"):
                return
        return super()._validate_sale_orders(order_filter)

    def _validate_pickings(self, picking_filter):
        if self.env.context.get("sale_workflow_job_delayed"):
            return
        return super()._validate_pickings(picking_filter)

    def _create_invoices(self, create_filter):
        if self.env.context.get("sale_workflow_job_delayed"):
            return
        return super()._validate_invoices(create_filter)

    # Missing dependency for 'invoice_status' on account.move ?
    # def _validate_invoices(self, validate_invoice_filter):
    #     if self.env.context.get("sale_workflow_job_delayed"):
    #         return
    #     return super()._validate_invoices(validate_invoice_filter)

    def _sale_done(self, sale_done_filter):
        if self.env.context.get("sale_workflow_job_delayed"):
            return
        return super()._sale_done(sale_done_filter)

    def _register_payments(self, payment_filter):
        if self.env.context.get("sale_workflow_job_delayed"):
            return
        return super()._register_payments(payment_filter)
