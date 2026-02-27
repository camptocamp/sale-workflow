# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_multiple_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Sales Multiple",
        compute="_compute_sale_multiple_uom_id",
        inverse="_inverse_sale_multiple_uom_id",
        store=True,
        help="When set, sale order quantities are rounded up to an "
        "multiple number of this unit.",
    )

    @api.depends("product_variant_ids", "product_variant_ids.sale_multiple_uom_id")
    def _compute_sale_multiple_uom_id(self):
        self.sale_multiple_uom_id = self.env["uom.uom"]
        for template in self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        ):
            template.sale_multiple_uom_id = (
                template.product_variant_ids.sale_multiple_uom_id
            )

    def _inverse_sale_multiple_uom_id(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.sale_multiple_uom_id = (
                    template.sale_multiple_uom_id
                )
