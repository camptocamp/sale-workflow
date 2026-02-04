# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class TestSaleProductMultipleQty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]
        cls.UoM = cls.env["uom.uom"]
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.base_uom = cls.env.ref("uom.product_uom_unit")
        cls.product_notebook = cls._create_product("Notebook")
        cls.product_screw = cls._create_product("Screw")
        cls.uom_pack_100 = cls._create_uom("Pack of 100", 100)
        # We sell notebooks in packs of 6 and 100 units, multiple 100
        cls.uom_pack_6 = cls._create_uom("Pack of 6", 6)
        # We sell screws in packs of 5 and 100 units, multiple 100
        cls.uom_pack_5 = cls._create_uom("Pack of 5", 5)
        # Set allowed UoMs and sales multiple UoM for notebooks
        cls.product_notebook.uom_ids = [
            Command.link(cls.uom_pack_6.id),
            Command.link(cls.uom_pack_100.id),
        ]
        cls.product_notebook.sale_multiple_uom_id = cls.uom_pack_100
        # Set allowed UoMs and sales multiple UoM for screws
        cls.product_screw.uom_ids = [
            Command.link(cls.uom_pack_5.id),
            Command.link(cls.uom_pack_100.id),
        ]
        cls.product_screw.sale_multiple_uom_id = cls.uom_pack_100
        # Create a sale order with both products
        cls._create_sale_order()
        # Make sure the lines use the intended UoMs
        # (product_uom_id is readonly in Form)
        cls.nb_line, cls.screw_line = cls.sale.order_line
        cls.nb_line.write({"product_uom_id": cls.uom_pack_6.id})
        cls.screw_line.write({"product_uom_id": cls.uom_pack_5.id})

    @classmethod
    def _create_product(cls, name):
        return cls.Product.create({"name": name, "type": "consu"})

    @classmethod
    def _create_uom(cls, name, factor):
        return cls.UoM.create(
            {
                "name": name,
                "relative_factor": factor,
                "relative_uom_id": cls.base_uom.id,
            }
        )

    @classmethod
    def _create_sale_order(cls):
        with Form(cls.env["sale.order"]) as sale:
            sale.partner_id = cls.partner
            with sale.order_line.new() as line:
                line.product_id = cls.product_notebook
            with sale.order_line.new() as line:
                line.product_id = cls.product_screw
        cls.sale = sale.save()

    def _get_incompatible_uom_warning_msg(self, order_line, entered_qty, rounded_qty):
        multiple_uom = order_line.product_id.sale_multiple_uom_id
        valid_qty = order_line._nearest_valid_integer_qty(entered_qty)
        return (
            "Incompatible UoMs.\n"
            f"The entered qty {entered_qty:.2f} is rounded to {rounded_qty:.2f} "
            f"which is not valid for product '{order_line.product_id.display_name}'.\n"
            f"It should be a multiple of {multiple_uom.display_name}.\n"
            f"The nearest valid qty is {valid_qty:.2f}."
        )

    def test_00_round_up_onchange(self):
        """Onchange rounds compatible UoMs and returns warning for incompatible ones."""
        # Compatible: Pack of 5 + multiple Pack of 100
        with Form(self.sale) as sale_order:
            with sale_order.order_line.edit(1) as line:
                line.product_uom_qty = 55
        sale = sale_order.save()
        screw_line = sale.order_line[1]
        self.assertEqual(screw_line.product_uom_qty, 60)

        # Incompatible: Pack of 6 + multiple Pack of 100
        # For warning checks, call onchange directly to capture its return dict.
        nb_line = sale.order_line[0]
        res = nb_line.onchange(
            {"product_uom_qty": 13}, ["product_uom_qty"], {"product_uom_qty": {}}
        )
        round_qty = nb_line._round_sale_qty_to_multiple(13)
        expected_msg = self._get_incompatible_uom_warning_msg(
            nb_line,
            entered_qty=13,
            rounded_qty=round_qty,
        )
        self.assertTrue(res)
        self.assertIn("warning", res)
        self.assertEqual(res["warning"]["title"], "Warning")
        self.assertEqual(res["warning"]["message"], expected_msg)

    def test_01_no_sale_multiple_uom_rounding(self):
        """Test if no sales multiple UoM, onchange does not modify qty."""
        self.product_notebook.sale_multiple_uom_id = False
        nb_line = self.sale.order_line[0]
        nb_line.write({"product_uom_id": self.uom_pack_6.id})

        with Form(self.sale) as sale_order:
            with sale_order.order_line.edit(0) as line:
                line.product_uom_qty = 13
        sale = sale_order.save()
        nb_line = sale.order_line[0]
        self.assertEqual(nb_line.product_uom_qty, 13)

    def test_02_constraint_on_incompatible_uom(self):
        """Test constraint when confirming sale order with incompatible UoMs."""
        nb_line = self.sale.order_line[0]
        nb_line.write({"product_uom_id": self.uom_pack_6.id})
        round_qty = nb_line._round_sale_qty_to_multiple(13)
        expected_msg = self._get_incompatible_uom_warning_msg(
            nb_line,
            entered_qty=13,
            rounded_qty=round_qty,
        )

        with self.assertRaises(ValidationError, msg=expected_msg):
            nb_line.write({"product_uom_qty": 13})
