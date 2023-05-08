# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields, models


class SaleWorkflowProcess(models.Model):
    _inherit = "sale.workflow.process"

    execute_every = fields.Integer(
        string="Run every (in seconds)",
        help="Sets a frequency for this workflow to be executed (in seconds)",
    )
    next_execution = fields.Datetime(readonly=True)
    check_creation_time = fields.Boolean(
        string="Enforce on creation time",
        help="When checked only sales created before the last execution will be processed.",
    )

    def write(self, vals):
        if "execute_every" in vals.keys():
            execute_every = vals["execute_every"]
            if execute_every == 0:
                vals["next_execution"] = False
            else:
                vals["next_execution"] = fields.Datetime.now() + timedelta(
                    seconds=execute_every
                )
        return super().write(vals)
