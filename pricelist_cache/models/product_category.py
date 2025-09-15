# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    product_ids = fields.One2many("product.product", "categ_id", string="Products")

