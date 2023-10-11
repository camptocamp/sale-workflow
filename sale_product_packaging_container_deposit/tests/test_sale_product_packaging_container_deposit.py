# Copyright 2023 Camptocamp (<https://www.camptocamp.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo.addons.product_packaging_container_deposit.tests.common import Common


class TestSaleProductPackagingContainerDeposit(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Copy packaging of product A to product B
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "packaging_ids": [(6, 0, [pack.copy().id for pack in cls.packaging])],
            }
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "Product Test C (No packaging)"}
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
                "name": self.product_a.name,
                "product_id": self.product_a.id,
                "product_uom_qty": 50,
            }
        )
        self.sale_order.action_confirm()
        self.sale_order._compute_order_product_packaging_quantity()
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id
            in self.product_a.mapped("packaging_ids.package_type_id.container_deposit")
        )
        self.assertEqual(len(deposit_lines), 0)

    def test_sale_product_packaging_container_deposit_quantities_case1(self):
        """
        Case 1: Product A | qty = 280. Result:
                280 // 240 = 1 => add SO line for 1 Pallet
                280 // 24 (biggest PACK) => add SO line for 11 boxes of 24
        """
        self.env["sale.order.line"].create(
            [
                {
                    "order_id": self.sale_order.id,
                    "name": self.product_a.name,
                    "product_id": self.product_a.id,
                    "product_uom_qty": 280,
                },
                {
                    "order_id": self.sale_order.id,
                    "name": self.product_c.name,
                    "product_id": self.product_c.id,
                    "product_uom_qty": 1,
                },
            ]
        )

        self.sale_order._compute_order_product_packaging_quantity()
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id
            in self.product_a.mapped("packaging_ids.package_type_id.container_deposit")
        )
        self.assertEqual(len(deposit_lines), 2)

        # 11 Boxes + 1 Pallet
        self.assertEqual(deposit_lines[1].product_uom_qty, 11.0)
        self.assertEqual(deposit_lines[0].product_uom_qty, 1.0)

    def test_sale_product_packaging_container_deposit_quantities_case2(self):
        """
        Case 2: Product A | qty = 280 and packaging=Box of 12. Result:
            280 // 240 = 1 => add SO line for 1 Pallet
            280 // 12 (forced packaging for Boxes) => add SO line for 23 boxes of 12
        """
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": self.product_a.name,
                "product_id": self.product_a.id,
                "product_uom_qty": 280,
                # Box of 12
                "product_packaging_id": self.packaging[0].id,
            },
        )
        self.sale_order._compute_order_product_packaging_quantity()
        # Filter lines with boxes
        deposit_line = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id
            == self.packaging[0].package_type_id.container_deposit
        )
        self.assertEqual(deposit_line.product_uom_qty, 23)

    def test_sale_product_packaging_container_deposit_quantities_case3(self):
        """
        Case 3: Product A & Product B. Both have a deposit of 1 box of 24. Result:
                Only one line for 2 boxes of 24
        """
        self.env["sale.order.line"].create(
            [
                {
                    "order_id": self.sale_order.id,
                    "name": self.product_a.name,
                    "product_id": self.product_a.id,
                    "product_uom_qty": 24,
                },
                {
                    "order_id": self.sale_order.id,
                    "name": self.product_b.name,
                    "product_id": self.product_b.id,
                    "product_uom_qty": 24,
                },
            ]
        )
        self.sale_order._compute_order_product_packaging_quantity()
        deposit_line = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id
            in self.product_a.mapped("packaging_ids.package_type_id.container_deposit")
        )
        self.assertEqual(deposit_line.name, "Box")
        self.assertEqual(deposit_line.product_uom_qty, 2.0)

    def test_sale_product_packaging_container_deposit_quantities_case4(self):
        """
        Case 4: Product A | qty = 24. Result:
                24 // 24 (biggest PACK) => add SO line for 1 box of 24
                Product A | Increase to 48. Result:
                48 // 24 (biggest PACK) =>  recompute previous SO line with 2 boxes of 24
                Add manually Product A container deposit (Box). Result:
                1 SO line with 2 boxes of 24 (System added)
                + 1 SO line with 1 box (manually added)
        """
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": self.product_a.name,
                "product_id": self.product_a.id,
                "product_uom_qty": 24,
            },
        )
        self.sale_order._compute_order_product_packaging_quantity()
        order_line.write({"product_uom_qty": 48})
        self.sale_order._compute_order_product_packaging_quantity()
        deposit_line = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id
            in self.product_a.mapped("packaging_ids.package_type_id.container_deposit")
        )
        self.assertEqual(deposit_line.name, "Box")
        self.assertEqual(deposit_line.product_uom_qty, 2.0)

        # Add manually 1 box
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": self.package_type_box.container_deposit.name,
                "product_id": self.package_type_box.container_deposit.id,
                "product_uom_qty": 1,
            }
        )
        self.sale_order._compute_order_product_packaging_quantity()
        # Filter lines with boxes
        deposit_lines = self.sale_order.order_line.filtered(
            lambda ol: ol.product_id
            == self.packaging[0].package_type_id.container_deposit
        )
        self.assertEqual(deposit_lines[1].product_uom_qty, 2)
        self.assertEqual(deposit_lines[0].product_uom_qty, 1)
