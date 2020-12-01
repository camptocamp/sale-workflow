# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from ..models.sale_coupon_program_option import DISCOUNT_PRODUCT_FNAME, SELF
from .common import TestSaleCouponProductManageCommon


class TestSaleCouponOptions(TestSaleCouponProductManageCommon):
    """Test class for program option use cases."""

    def test_01_get_program_values(self):
        """Return program values from discount_fixed_amount option."""
        values = self.program_option_fixed_amount.get_program_values()
        self.assertEqual(
            values,
            {
                SELF: {"reward_type": "discount", "discount_type": "fixed_amount"},
                DISCOUNT_PRODUCT_FNAME: {},
            },
        )

    def test_02_get_program_values(self):
        """Return program values from product_sale_ok option."""
        values = self.program_option_sale_ok.get_program_values()
        self.assertEqual(values, {SELF: {}, DISCOUNT_PRODUCT_FNAME: {"sale_ok": True}})

    def test_03_get_program_values(self):
        """Return program values from product_not_sale_ok option."""
        values = self.program_option_not_sale_ok.get_program_values()
        self.assertEqual(values, {SELF: {}, DISCOUNT_PRODUCT_FNAME: {"sale_ok": False}})

    def test_04_get_program_values(self):
        """Return program values from multiple options.

        Case 1: discount_fixed_amount + product_sale_ok
        Case 2: discount_fixed_amount + product_not_sale_ok
        Case 3: discount_fixed_amount (with program rec) + product_not_sale_ok
        """
        # Case 1.
        values = (
            self.program_option_fixed_amount | self.program_option_sale_ok
        ).get_program_values()
        self.assertEqual(
            values,
            {
                SELF: {"reward_type": "discount", "discount_type": "fixed_amount"},
                DISCOUNT_PRODUCT_FNAME: {"sale_ok": True},
            },
        )
        # Case 2.
        values = (
            self.program_option_fixed_amount | self.program_option_not_sale_ok
        ).get_program_values()
        self.assertEqual(
            values,
            {
                SELF: {"reward_type": "discount", "discount_type": "fixed_amount"},
                DISCOUNT_PRODUCT_FNAME: {"sale_ok": False},
            },
        )
        # Case 3.
        values = (
            self.program_option_fixed_amount | self.program_option_not_sale_ok
        ).get_program_values(program=self.program_coupon_1)
        self.assertEqual(
            values,
            {
                SELF: {"reward_type": "discount", "discount_type": "fixed_amount"},
                DISCOUNT_PRODUCT_FNAME: {
                    "sale_ok": False,
                    "list_price": self.program_coupon_1.discount_fixed_amount,
                },
            },
        )

    def test_05_get_program_values(self):
        """Try to return program values from incompatible options.

        Case 1: incompatible by option type.
        Case 2: incompatible by program type.
        """
        # Case 1.
        values = (
            self.program_option_fixed_amount
            | self.program_option_sale_ok
            | self.program_option_not_sale_ok
        ).get_program_values()
        self.assertEqual(values, {})
        # Case 2.
        self.program_option_fixed_amount.program_type = "promotion_program"
        values = (
            self.program_option_fixed_amount | self.program_option_sale_ok
        ).get_program_values()
        self.assertEqual(values, {})
