# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _has_only_lines_to_split(self, lines_to_split):
        return self.order_line.filtered(lambda l: not l.is_delivery) == lines_to_split
