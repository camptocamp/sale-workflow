# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from lxml import etree

from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests.common import new_test_user, users

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
from odoo.addons.sale.tests.common import TestSaleCommonBase


class TestSaleConfirmSecurityGroup(TestSaleCommonBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        sale_group = "sales_team.group_sale_salesman"
        cls.user_with_group = new_test_user(
            cls.env,
            login="test-sale-user-with-confirm-group",
            groups=f"{sale_group},sale_confirm_security_group.group_can_confirm_sale",
        )
        cls.user_without_group = new_test_user(
            cls.env,
            login="test-sale-user-without-confirm-group",
            groups=sale_group,
        )
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    def _create_sale(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    Command.create(
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
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, "sale")

    @users("test-sale-user-without-confirm-group")
    def test_user_without_group_cannot_confirm(self):
        sale_order = self._create_sale()
        with self.assertRaisesRegex(ValidationError, "You cannot confirm a Sale Order"):
            sale_order.action_confirm()

    @users("test-sale-user-without-confirm-group")
    def test_user_without_group_cannot_see_confirm_button(self):
        form_view = self.env["sale.order"].get_view(view_type="form")
        arch = etree.fromstring(form_view["arch"])
        for button_node in arch.xpath("//button[@name='action_confirm']"):
            self.assertEqual(button_node.get("invisible"), "1")
