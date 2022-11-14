# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    customer_ref = fields.Char("Customer Ref.")
