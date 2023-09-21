# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo.tests import common


class TestSaleProductPackagingContainerDeposit(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.container_deposit = cls.env["product.product"].create(
            {"name": "Container Product Test"}
        )
        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "Super Package Type",
                "container_deposit": cls.container_deposit.id,
            }
        )
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product Test 1",
                "packaging_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Packaging Test",
                            "qty": 24.0,
                            "package_type_id": cls.package_type.id,
                        },
                    )
                ],
            }
        )

        cls.product2 = cls.env["product.product"].create(
            {"name": "Product Test 2 (No packaging)"}
        )
        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Product Test 1",
                "packaging_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Packaging Test",
                            "qty": 24.0,
                            "package_type_id": cls.package_type.id,
                        },
                    )
                ],
            }
        )

        cls.sale_order = cls.env["sale.order"].create(
            {
                "company_id": cls.env.company.id,
                "partner_id": cls.env.ref("base.res_partner_12").id,
            }
        )

    def test_confirmed_sale_product_packaging_container_deposit_quantities(self):
        """Container deposit is added only draft orders"""
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": self.product1.name,
                "product_id": self.product1.id,
                "product_uom_qty": 50,
            }
        )
        self.sale_order.action_confirm()
        self.sale_order._compute_sale_product_packaging_quantity()
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id == self.container_deposit
        )
        self.assertEqual(len(deposit_lines), 0)

    def test_sale_product_packaging_container_deposit_quantities(self):
        self.env["sale.order.line"].create(
            [
                {
                    "order_id": self.sale_order.id,
                    "name": self.product1.name,
                    "product_id": self.product1.id,
                    "product_uom_qty": 50,
                },
                {
                    "order_id": self.sale_order.id,
                    "name": self.product2.name,
                    "product_id": self.product2.id,
                    "product_uom_qty": 1,
                },
            ]
        )

        self.sale_order._compute_sale_product_packaging_quantity()
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id == self.container_deposit
        )
        self.assertEqual(len(deposit_lines), 1)
        self.assertEqual(deposit_lines.product_uom_qty, 2)

        # Add more Product Test => Container Product Test will increase
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": self.product1.name,
                "product_id": self.product1.id,
                "product_uom_qty": 50,
            }
        )
        self.sale_order._compute_sale_product_packaging_quantity()
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id == self.container_deposit
        )
        self.assertEqual(len(deposit_lines), 1)
        self.assertEqual(deposit_lines.product_uom_qty, 4)

        # Add Container Product Test manually
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": self.container_deposit.name,
                "product_id": self.container_deposit.id,
                "product_uom_qty": 1,
            }
        )
        self.sale_order._compute_sale_product_packaging_quantity()
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id == self.container_deposit
        )
        # With container product test added manually, we have 2 container deposit lines
        # (1 added by the system and another added manually)
        self.assertEqual(len(deposit_lines), 2)
