# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class SaleOrderSplitStrategy(models.Model):
    _name = "sale.order.split.strategy"
    _description = "Order split strategy"
    _order = "sequence,name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    line_filter_id = fields.Many2one(
        "ir.filters",
        domain="[('model_id', '=', 'sale.order.line')]",
        required=True,
    )
    copy_sections = fields.Boolean()
    copy_notes = fields.Boolean()
