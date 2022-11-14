# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form, SavepointCase


class TestSaleLineCustomerRef(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.wh.delivery_steps = "pick_pack_ship"
        cls.order = cls._create_order()
        cls.order.action_confirm()

    @classmethod
    def _create_order(cls):
        # Create a SO with two lines sharing the same product but two
        # different customer references
        with Form(cls.env["sale.order"]) as form:
            form.partner_id = cls.env.ref("base.res_partner_1")
            for i in range(2):
                with form.order_line.new() as line:
                    line.product_id = cls.env.ref("product.consu_delivery_01")
                    line.customer_ref = f"TEST_{i}"
            order = form.save()
            return order

    def test_customer_ref(self):
        # Ensure we have two moves that didn't get merged despite the identical
        # product as their customer reference is different.
        self.assertEqual(len(self.order.order_line.move_ids), 2)
        # Check customer ref. among chained moves of all SO lines
        for i in range(2):
            order_line = self.order.order_line[i]
            expected_ref = f"TEST_{i}"
            self.assertEqual(order_line.customer_ref, expected_ref)
            # Customer reference is propagated on the ship move
            move_ship = order_line.move_ids
            self.assertEqual(move_ship.customer_ref, expected_ref)
            # And on the pack and pick moves
            move_pack = move_ship.move_orig_ids
            self.assertEqual(move_pack.customer_ref, expected_ref)
            move_pick = move_pack.move_orig_ids
            self.assertEqual(move_pick.customer_ref, expected_ref)
