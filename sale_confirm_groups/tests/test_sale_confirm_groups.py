# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import users

from .common import TestSaleConfirmGroupsCommon


class TestSaleConfirmGroups(TestSaleConfirmGroupsCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Dummy customer for SO creation
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    def _create_sale(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    fields.Command.create(
                        {
                            "name": "Product",
                            "product_id": self.env.ref("product.consu_delivery_01").id,
                            "product_uom_qty": 1,
                            "price_unit": 50.00,
                        }
                    )
                ],
            }
        )

    @users("test-sale-user-with-confirm-group")
    def test_user_with_group_can_confirm(self):
        sale_order = self._create_sale()
        self.assertTrue(sale_order.user_can_confirm)
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, "sale")

    @users("test-sale-user-without-confirm-group")
    def test_user_without_group_cannot_confirm(self):
        sale_order = self._create_sale()
        self.assertFalse(sale_order.user_can_confirm)
        with self.assertRaises(ValidationError) as error:
            sale_order.action_confirm()
        self.assertEqual(
            error.exception.args[0],
            f"User {self.env.user.name} cannot confirm Sale Orders",
        )
