# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def prepare_order_lines_with_deposit_container_values(
        self, deposit_container_qties
    ):
        values = []
        for package_level in deposit_container_qties:
            for product in deposit_container_qties[package_level]:
                values.append(
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom_qty": deposit_container_qties[package_level][
                                product
                            ],
                            "system_added": True,
                        },
                    )
                )
        return values

    @api.depends("order_line.product_uom_qty", "order_line.product_packaging_id")
    def _compute_sale_product_packaging_quantity(self):
        self.ensure_one()
        if self.state != "draft":
            return

        # Reset existing deposit lines (only the ones automatically added)
        existing_deposit_lines = self.order_line.filtered(
            lambda order_line: order_line.system_added
        )
        existing_deposit_lines.unlink()

        # Lines to compute container deposit
        lines_to_comp_deposit = self.order_line.filtered(
            lambda order_line: order_line.product_packaging_id.package_type_id.container_deposit
            or order_line.product_id.packaging_ids
        )
        deposit_container_qties = (
            lines_to_comp_deposit._get_order_lines_container_deposit_quantities()
        )
        order_line_vals = self.prepare_order_lines_with_deposit_container_values(
            deposit_container_qties
        )
        self.write({"order_line": order_line_vals})


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    system_added = fields.Boolean(
        default=False, help="Line automaticaly added by the system"
    )

    def _get_order_lines_container_deposit_quantities(self):
        """
        Returns a dict with quantity of product(container deposit)
        per package level for a set of lines
        {
            package_level: {
                container_deposit_product: quantity
                }
        }
        """
        deposit_product_qties = {
            package_level_id: {}
            for package_level_id in self.mapped(
                "product_id.packaging_ids.packaging_level_id"
            )
        }

        for line in self:
            line_deposit_qties = (
                line.product_id.get_product_container_deposit_quantities(
                    line.product_uom_qty
                )
            )
            for package_level in line_deposit_qties:
                if deposit_product_qties[package_level].get(
                    line_deposit_qties[package_level][0], False
                ):
                    deposit_product_qties[package_level][
                        line_deposit_qties[package_level][0]
                    ] += line_deposit_qties[package_level][1]
                else:
                    deposit_product_qties[package_level][
                        line_deposit_qties[package_level][0]
                    ] = line_deposit_qties[package_level][1]
        return deposit_product_qties
