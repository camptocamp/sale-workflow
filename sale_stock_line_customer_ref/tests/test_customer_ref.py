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
        # Create a SO with 4 lines sharing the same product but with 2 different
        # customer references.
        product = cls.env.ref("product.consu_delivery_01")
        with Form(cls.env["sale.order"]) as form:
            form.partner_id = cls.env.ref("base.res_partner_1")
            for i in range(4):
                with form.order_line.new() as line:
                    line.product_id = product
                    line.customer_ref = f"TEST_{i % 2}"
                    line.product_uom = product.uom_id
                    line.product_uom_qty = 1
            order = form.save()
            return order

    def test_customer_ref(self):
        # Ship moves can't be merged anyway in std Odoo as they belong to
        # different SO lines, but chained moves not linked directly to
        # the SO lines can still be merged based on the customer reference.
        self.assertEqual(len(self.order.order_line), 4)
        self.assertEqual(len(self.order.order_line.move_ids), 4)
        # Check customer ref. among chained moves of all SO lines
        for i in range(4):
            expected_ref = f"TEST_{i % 2}"
            order_line = self.order.order_line[i]
            order_lines_same_ref = self.order.order_line.filtered_domain(
                [("customer_ref", "=", expected_ref)]
            )
            self.assertEqual(order_line.customer_ref, expected_ref)
            # Customer reference is propagated on the ship move
            move_ship = order_line.move_ids
            self.assertEqual(move_ship.customer_ref_sale_line_id, order_line)
            self.assertEqual(move_ship.customer_ref, expected_ref)
            self.assertEqual(move_ship.product_uom_qty, 1)
            # And on the pack and pick moves have been merged based on
            # the propagated customer reference.
            move_pack = move_ship.move_orig_ids
            self.assertIn(move_pack.customer_ref_sale_line_id, order_lines_same_ref)
            self.assertEqual(move_pack.customer_ref, expected_ref)
            self.assertEqual(move_pack.product_uom_qty, 2)
            move_pick = move_pack.move_orig_ids
            self.assertIn(move_pick.customer_ref_sale_line_id, order_lines_same_ref)
            self.assertEqual(move_pick.customer_ref, expected_ref)
            self.assertEqual(move_pick.product_uom_qty, 2)

    def test_has_customer_ref(self):
        for picking in self.order.picking_ids:
            self.assertTrue(picking.has_customer_ref)
