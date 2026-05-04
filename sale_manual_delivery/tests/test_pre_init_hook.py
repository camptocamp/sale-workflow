# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import TransactionCase

from odoo.addons.sale_manual_delivery.hook import pre_init_hook


class TestPreInitHook(TransactionCase):
    """Non-regression tests for the ``pre_init_hook`` SQL update.

    The hook recomputes ``qty_procured`` / ``qty_to_procure`` directly in SQL
    on existing ``sale_order_line`` records, to avoid a full Python recompute
    when the module is installed on a database that already has confirmed
    sales orders.

    These tests build their own sales orders / stock moves and assert only on
    those records, so the suite is robust to whatever pre-existing data the
    target database may contain.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Pre-Init Hook Partner"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Pre-Init Hook Product",
                "type": "consu",
                "is_storable": True,
                "list_price": 10.0,
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 1000
        )

    def _create_order(self, qty, manual_delivery=False):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "manual_delivery": manual_delivery,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

    def _run_manual_delivery(self, order, qty):
        wizard = (
            self.env["manual.delivery"]
            .with_context(active_model=order._name, active_ids=order.ids)
            .create({})
        )
        wizard.line_ids.write({"quantity": qty})
        wizard.confirm()

    def _validate_picking(self, picking, qty):
        picking.action_assign()
        picking.move_line_ids.write({"quantity": qty})
        picking.button_validate()

    def _read_qty(self, line):
        """Read raw column values, bypassing the ORM compute trigger."""
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT qty_procured, qty_to_procure "
            "FROM sale_order_line WHERE id = %s",
            (line.id,),
        )
        return self.env.cr.fetchone()

    def _reset_qty(self, lines):
        """Set columns to NULL to simulate the state right after the
        ALTER TABLE in the hook (column added but not yet populated)."""
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE sale_order_line "
            "SET qty_procured = NULL, qty_to_procure = NULL "
            "WHERE id IN %s",
            (tuple(lines.ids),),
        )
        self.env.invalidate_all()

    def test_pre_init_hook_fully_delivered(self):
        """Standard order, picking validated for the full quantity.

        Expected: qty_procured = ordered qty, qty_to_procure = 0.
        """
        order = self._create_order(qty=10, manual_delivery=False)
        order.action_confirm()
        self.assertTrue(order.picking_ids)
        self._validate_picking(order.picking_ids, qty=10)
        line = order.order_line

        self._reset_qty(line)
        pre_init_hook(self.env)

        qty_procured, qty_to_procure = self._read_qty(line)
        self.assertEqual(qty_procured, 10.0)
        self.assertEqual(qty_to_procure, 0.0)

    def test_pre_init_hook_partially_delivered(self):
        """Manual delivery order, wizard called and picking validated for
        a partial quantity.

        Expected: qty_procured = partial qty, qty_to_procure = remaining.
        """
        order = self._create_order(qty=10, manual_delivery=True)
        order.action_confirm()
        self.assertFalse(order.picking_ids)
        self._run_manual_delivery(order, qty=4)
        self.assertEqual(len(order.picking_ids), 1)
        self._validate_picking(order.picking_ids, qty=4)
        line = order.order_line

        self._reset_qty(line)
        pre_init_hook(self.env)

        qty_procured, qty_to_procure = self._read_qty(line)
        self.assertEqual(qty_procured, 4.0)
        self.assertEqual(qty_to_procure, 6.0)

    def test_pre_init_hook_nothing_delivered_no_moves(self):
        """Manual delivery order, confirmed but no wizard call: no stock
        moves are linked to the line.

        The hook's INNER JOIN on stock_move means lines without any move
        are *not* updated. The values should stay NULL (the hook must not
        crash on such lines either).
        """
        order = self._create_order(qty=10, manual_delivery=True)
        order.action_confirm()
        line = order.order_line
        self.assertFalse(line.move_ids)

        self._reset_qty(line)
        pre_init_hook(self.env)

        qty_procured, qty_to_procure = self._read_qty(line)
        self.assertIsNone(qty_procured)
        self.assertIsNone(qty_to_procure)

    def test_pre_init_hook_procured_not_yet_delivered(self):
        """Standard order, picking created on confirm but not yet validated.

        The stock move exists with state != 'cancel', so the hook should
        count it as procured even though no quantity has actually been
        shipped to the customer.
        """
        order = self._create_order(qty=7, manual_delivery=False)
        order.action_confirm()
        self.assertTrue(order.picking_ids)
        self.assertNotEqual(order.picking_ids.state, "done")
        line = order.order_line

        self._reset_qty(line)
        pre_init_hook(self.env)

        qty_procured, qty_to_procure = self._read_qty(line)
        self.assertEqual(qty_procured, 7.0)
        self.assertEqual(qty_to_procure, 0.0)

    def test_pre_init_hook_partially_procured_manual_delivery(self):
        """Manual delivery order, wizard called for a partial quantity but
        picking *not* validated.

        Stock moves exist for the partial qty (state 'assigned' or
        'confirmed'). The hook should treat them as procured.
        """
        order = self._create_order(qty=10, manual_delivery=True)
        order.action_confirm()
        self._run_manual_delivery(order, qty=3)
        self.assertEqual(len(order.picking_ids), 1)
        self.assertNotEqual(order.picking_ids.state, "done")
        line = order.order_line

        self._reset_qty(line)
        pre_init_hook(self.env)

        qty_procured, qty_to_procure = self._read_qty(line)
        self.assertEqual(qty_procured, 3.0)
        self.assertEqual(qty_to_procure, 7.0)
