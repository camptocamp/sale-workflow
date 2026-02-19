# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_additionnal_combination_info(
        self, product_or_template, quantity, uom, date, website
    ):
        # OVERRIDE: to update the combination info with the multiple related info
        combination_info = super()._get_additionnal_combination_info(
            product_or_template, quantity, uom, date, website
        )

        if not product_or_template.sale_multiple_uom_id:
            return combination_info
        rounding = "UP"
        if to_rounding := self.env.context.get("multiple_rounding"):
            rounding = to_rounding
        rounded_qty = self.sale_multiple_uom_id._check_qty(
            quantity, self.uom_id, rounding_method=rounding
        )
        combination_info.update(
            {
                "is_multiple": 1,
                # The website expects an integer value as an input
                # ``website_sale::variant_mixin.js``
                # parseInt(parent.querySelector('input[name="add_qty"]').value).
                "multiple_qty": int(rounded_qty),
            }
        )
        return combination_info
