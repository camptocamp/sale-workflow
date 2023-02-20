# Copyright 2020 Tecnativa - Carlos Roca
# Copyright 2023 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Allowed Products",
        compute="_compute_product_assortment_ids",
    )
    has_allowed_products = fields.Boolean(compute="_compute_product_assortment_ids")

    @api.depends("partner_id", "partner_shipping_id", "partner_invoice_id")
    def _compute_product_assortment_ids(self):
        self.allowed_product_ids = False
        self.has_allowed_products = False
        partner_field = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_order_product_assortment.partner_field", "partner_id")
        )
        product_domain = []
        if self[partner_field]:
            filters_partner_domain = self.env["ir.filters"].search(
                [("is_assortment", "=", True)]
            )
            for ir_filter in filters_partner_domain:
                if self[partner_field] & ir_filter.all_partner_ids:
                    product_domain = expression.AND(
                        [product_domain, ir_filter._get_eval_domain()]
                    )
            if product_domain:
                self.allowed_product_ids = self.env["product.product"].search(
                    product_domain
                )
                self.has_allowed_products = True
