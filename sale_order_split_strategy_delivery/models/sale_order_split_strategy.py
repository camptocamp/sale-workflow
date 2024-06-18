# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models
from odoo.osv.expression import AND


class SaleOrderSplitStrategy(models.Model):
    _inherit = "sale.order.split.strategy"

    def _get_lines_to_split_domain(self, orders):
        domain = super()._get_lines_to_split_domain(orders)
        return AND([domain, [("is_delivery", "=", False)]])
