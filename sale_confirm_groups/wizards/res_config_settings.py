# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class Settings(models.TransientModel):
    _inherit = "res.config.settings"

    can_confirm_sales_groups_ids = fields.Many2many(
        "res.groups",
        related="company_id.can_confirm_sales_groups_ids",
        readonly=False,
    )
