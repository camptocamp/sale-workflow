# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class FakeSaleOrder(models.Model):
    _inherit = "sale.order"  # pylint: disable=consider-merging-classes-inherited

    dummy_sale_ids = fields.Many2many(
        "sale.order",
        relation="dummy_sale2sale_m2m",
        column1="dummy_sale_col1_id",
        column2="dummy_sale_col2_id",
    )
    dummy_user_ids = fields.Many2many(
        "res.users",
        relation="dummy_sale2user_m2m",
        column1="dummy_sale_col1_id",
        column2="dummy_user_col2_id",
    )
