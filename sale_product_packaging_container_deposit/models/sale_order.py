# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "order.mixin"]

class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "order.line.mixin"]
