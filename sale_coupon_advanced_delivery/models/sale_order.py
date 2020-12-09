# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    """Extend to make promotions recompute aware of delivery lines."""

    _inherit = "sale.order"

    def get_update_pricelist_order_lines(self):
        """Extend to ignore delivery lines."""
        order_lines = super().get_update_pricelist_order_lines()
        return order_lines.filtered(lambda r: not r.is_delivery)
