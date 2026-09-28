# Copyright 2024 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        return super(
            SaleOrderLine,
            self.filtered(lambda line: not line.order_id.delivery_block_id),
        )._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)

    def _create_procurements(self, product_qty, procurement_uom, values):
        allowed = not self.order_id.delivery_block_id
        if not allowed:
            return []
        return super()._create_procurements(product_qty, procurement_uom, values)
