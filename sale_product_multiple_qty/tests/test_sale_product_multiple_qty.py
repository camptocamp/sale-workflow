# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, TransactionCase


class TestSaleProductMultipleQty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]
        cls.UoM = cls.env["uom.uom"]
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.base_uom = cls.env.ref("uom.product_uom_unit")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.product_notebook = cls._create_product("Notebook")
        cls.product_screw = cls._create_product("Screw")
        cls.product_table = cls._create_product("Table")
        cls.product_liquid = cls._create_product("Liquid")
        cls.uom_pack_100 = cls._create_uom("Pack of 100", 100, cls.base_uom)
        # We sell tables in packs of 10 and 100 units, multiple 100
        cls.uom_pack_10 = cls._create_uom("Pack of 10", 10, cls.base_uom)
        # We sell notebooks in packs of 6 and 100 units, multiple 100
        # (100 is NOT divisible by 6 → fractional result → ceil to integer)
        cls.uom_pack_6 = cls._create_uom("Pack of 6", 6, cls.base_uom)
        # We sell screws in packs of 5 and 100 units, multiple 100
        # (100 IS divisible by 5 → clean integer result)
        cls.uom_pack_5 = cls._create_uom("Pack of 5", 5, cls.base_uom)
        cls.uom_400g = cls._create_uom("400g", 0.4, cls.uom_kg)
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
        # Set allowed UoMs and sales multiple UoM for tables
        cls.product_table.uom_ids = [
            Command.link(cls.uom_pack_10.id),
            Command.link(cls.uom_pack_100.id),
        ]
        cls.product_table.sale_multiple_uom_id = cls.uom_pack_100
        # Set allowed UoMs and sales multiple UoM for liquid
        cls.product_liquid.uom_ids = [
            Command.link(cls.uom_400g.id),
        ]
        cls.product_liquid.sale_multiple_uom_id = cls.uom_kg
        # Create a sale order with all four products
        cls._create_sale_order()
        # Force the intended UoMs on each line
        # (product_uom_id is readonly in Form)
        cls.nb_line, cls.screw_line, cls.table_line, cls.liquid_line = (
            cls.sale.order_line
        )
        cls.nb_line.write({"product_uom_id": cls.uom_pack_6.id})
        cls.screw_line.write({"product_uom_id": cls.uom_pack_5.id})
        cls.table_line.write({"product_uom_id": cls.uom_pack_10.id})
        cls.liquid_line.write({"product_uom_id": cls.uom_400g.id})

    @classmethod
    def _create_product(cls, name):
        return cls.Product.create({"name": name, "type": "consu"})

    @classmethod
    def _create_uom(cls, name, factor, relative_uom_id):
        return cls.UoM.create(
            {
                "name": name,
                "relative_factor": factor,
                "relative_uom_id": relative_uom_id.id,
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
            with sale.order_line.new() as line:
                line.product_id = cls.product_table
            with sale.order_line.new() as line:
                line.product_id = cls.product_liquid
        cls.sale = sale.save()

    def test_00_round_up_compatible_uoms(self):
        """Onchange rounds UP to a clean integer for compatible Unit UoMs.

        Pack of 5 / sales multiple Pack of 100:
        100 is divisible by 5 → result is always a clean integer.
        - 55 packs of 5 → 60 packs of 5 (3 × Pack of 100)

        Pack of 10 / sales multiple Pack of 100:
        100 is divisible by 10 → result is always a clean integer.
        - 4 packs of 10 → 10 packs of 10 (1 × Pack of 100)
        """
        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(1) as line:
                line.product_uom_qty = 55
        sale = sale_form.save()
        self.assertEqual(sale.order_line[1].product_uom_qty, 60)

        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(2) as line:
                line.product_uom_qty = 4
        sale = sale_form.save()
        self.assertEqual(sale.order_line[2].product_uom_qty, 10)

    def test_01_round_up_incompatible_uoms_ceil_to_integer(self):
        """Onchange ceils to the next integer for incompatible Unit UoMs.

        Pack of 6 / sales multiple Pack of 100:
        raw step = 16.666...
        effective step = 17

        - 13 packs of 6 -> 17
        - 17 is already one valid step -> unchanged
        - 34 is already two valid steps -> unchanged
        - 35 rounds up to 50 (3 × Pack of 100 = 300 units = 50 packs of 6)
        """
        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = 13
        sale = sale_form.save()
        self.assertEqual(sale.order_line[0].product_uom_qty, 17)

        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = 17
        sale = sale_form.save()
        self.assertEqual(sale.order_line[0].product_uom_qty, 17)

        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = 34
        sale = sale_form.save()
        self.assertEqual(sale.order_line[0].product_uom_qty, 34)

        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = 35
        sale = sale_form.save()
        self.assertEqual(sale.order_line[0].product_uom_qty, 50)

    def test_02_no_rounding_when_already_multiple(self):
        """Onchange does not modify a qty that is already a valid multiple."""
        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(1) as line:
                line.product_uom_qty = 20
        sale = sale_form.save()
        self.assertEqual(sale.order_line[1].product_uom_qty, 20)

    def test_03_no_sale_multiple_uom_no_rounding(self):
        """Without a Sales Multiple UoM set, the onchange must not touch qty."""
        self.product_notebook.sale_multiple_uom_id = False
        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = 13
        sale = sale_form.save()
        self.assertEqual(sale.order_line[0].product_uom_qty, 13)

    def test_04_no_ceil_for_non_unit_reference_uoms(self):
        """Fractional qty is preserved for UoMs not sharing the Unit reference.

        Pack of 400g / sales multiple Pack of 1kg:
        1 kg is NOT divisible by 400g → rounds to 2.5 packs.
        """
        # Verify UoMs doesn't share the Unit reference
        self.assertFalse(self.liquid_line._sale_multiple_uom_has_unit_reference())

        # 2 × 400g → 2.5 × 400g (fractional, must NOT be ceiled to 3)
        with Form(self.sale) as sale_form:
            with sale_form.order_line.edit(3) as line:
                line.product_uom_qty = 2
        sale = sale_form.save()
        self.assertEqual(sale.order_line[3].product_uom_qty, 2.5)
