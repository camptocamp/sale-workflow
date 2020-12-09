# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import common


class TestDeliveryLinePrice(common.SavepointCase):
    """Test class for delivery line price extension."""

    @classmethod
    def setUpClass(cls):
        """Set up data for tests."""
        super().setUpClass()
        cls.ChooseDeliveryCarrier = cls.env["choose.delivery.carrier"]
        cls.sale_3 = cls.env.ref("sale.sale_order_3")
        cls.delivery_normal = cls.env.ref("delivery.normal_delivery_carrier")
        # Make it free if above threshold.
        cls.delivery_normal.write({"free_over": True, "amount": 100})
        cls.choose_delivery_carrier = cls.ChooseDeliveryCarrier.create(
            {"order_id": cls.sale_3.id, "carrier_id": cls.delivery_normal.id}
        )

    def test_01_test_delivery_line_price(self):
        """Recompute SO to see if delivery price not reset.

        Case 1: add delivery line
        Case 2: recompute promotions.
        """
        # Price must not changed, because delivery price must be 0 (
        # SO amount is over threshold).
        amount_total = self.sale_3.amount_total
        # Case 1.
        self.choose_delivery_carrier.button_confirm()
        self.assertEqual(self.sale_3.amount_total, amount_total)
        # Case 2.
        self.sale_3.recompute_coupon_lines()
        self.assertEqual(self.sale_3.amount_total, amount_total)
