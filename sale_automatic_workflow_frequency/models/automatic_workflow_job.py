# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime, timedelta

from odoo import api, models


class AutomaticWorkflowJob(models.Model):
    _inherit = "automatic.workflow.job"

    def run_with_workflow(self, sale_workflow):
        res = super().run_with_workflow(sale_workflow)
        if sale_workflow.execute_every:
            sale_workflow.next_execution = datetime.now() + timedelta(
                seconds=sale_workflow.execute_every
            )
        return res

    @api.model
    def _workflow_process_to_run_domain(self):
        return [
            "|",
            ("execute_every", "=", 0),
            "|",
            "&",
            ("execute_every", ">", 0),
            ("next_execution", "<=", datetime.now()),
            ("next_execution", "=", False),
        ]

    def _sale_workflow_domain(self, workflow):
        domain = super()._sale_workflow_domain(workflow)
        if workflow.check_creation_time:
            domain.append(
                (
                    "create_date",
                    "<",
                    datetime.now() - timedelta(seconds=workflow.execute_every),
                )
            )
        return domain
