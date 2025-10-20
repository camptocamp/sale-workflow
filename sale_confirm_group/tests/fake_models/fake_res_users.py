# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class FakeResUsers(models.Model):
    _inherit = "res.users"

    dummy_sale_ids = fields.Many2many(
        "sale.order",
        relation="dummy_sale2user_m2m",
        column1="dummy_user_col2_id",
        column2="dummy_sale_col1_id",
    )

    def action_confirm(self):
        return self
