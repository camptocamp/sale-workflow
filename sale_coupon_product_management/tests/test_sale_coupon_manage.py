# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form

from .common import (
    CODE_COUPON_PROGRAM,
    NAME_COUPON_PROGRAM,
    TestSaleCouponProductManageCommon,
)


class TestSaleCouponManage(TestSaleCouponProductManageCommon):
    """Test class for program management use cases."""

    def test_01_program_discount_product_rel_vals(self):
        """Check created program with related product.

        Check if related values are propagated to related product.

        Case 1: create promotion initially.
        Case 2: update promotion/related product related values.
        """
        # Case 1.
        program = self.program_coupon_1
        product = program.discount_line_product_id
        self.assertEqual(product.default_code, CODE_COUPON_PROGRAM)
        self.assertEqual(product.categ_id, self.product_category_coupon)
        # Must match program name exactly.
        self.assertEqual(product.name, NAME_COUPON_PROGRAM)
        # Case 2.
        name_2 = "Product Name"
        # Clear context, so it would be treated as separate update.
        product = product.with_context(forced_product_vals={})
        product.name = name_2
        self.assertEqual(program.name, NAME_COUPON_PROGRAM)
        self.assertEqual(product.name, name_2)
        name_3 = "Program Name"
        program.name = name_3
        self.assertEqual(program.name, name_3)
        self.assertEqual(product.name, name_3)
        # Make sure old dependencies dont update name the old way.
        program.discount_fixed_amount = 300
        self.assertEqual(program.name, name_3)
        self.assertEqual(product.name, name_3)
        code_2 = "MYCODE321"
        program.related_product_default_code = code_2
        self.assertEqual(product.default_code, code_2)
        program.discount_line_product_id.default_code = CODE_COUPON_PROGRAM
        self.assertEqual(product.default_code, CODE_COUPON_PROGRAM)
        # Sanity check.
        self.assertFalse(product.sale_ok)

    def test_02_program_discount_product_rel_vals(self):
        """Check if option values are passed to product.

        Case: on program create - passing sale_ok, list_price.
        """
        options = self.program_option_sale_ok | self.program_option_fixed_amount
        self.product_category_coupon.program_option_ids = [(6, 0, options.ids)]
        program = self.SaleCouponProgram.create(
            {
                "name": "Coupon Program 2",
                "program_type": "coupon_program",
                "reward_type": "discount",
                "discount_type": "fixed_amount",
                "discount_fixed_amount": 1000,
                "related_product_default_code": CODE_COUPON_PROGRAM,
                "related_product_categ_id": self.product_category_coupon.id,
            }
        )
        product = program.discount_line_product_id
        self.assertTrue(product.sale_ok)
        self.assertEqual(product.list_price, 1000)

    def test_03_check_program_options(self):
        """Validate if program values match its related options.

        Case 1: values match.
        Case 2: values not match.
        """
        # Case 1.
        # Unset to trigger constraint check.
        self.program_coupon_1.related_product_categ_id = False
        product = self.program_coupon_1.discount_line_product_id
        product.sale_ok = True  # to not trigger constraint on product.
        self.product_category_coupon.program_option_ids = [
            (6, 0, (self.program_option_fixed_amount | self.program_option_sale_ok).ids)
        ]
        try:
            self.program_coupon_1.related_product_categ_id = (
                self.product_category_coupon.id
            )
        except UserError:
            self.fail("Must not raise when program matches option values.")
        # Case 2.
        with self.assertRaises(UserError):
            self.program_coupon_1.discount_type = "percentage"
        with self.assertRaises(UserError):
            self.program_coupon_1.reward_type = "product"

    def test_04_check_product_options(self):
        """Validate if program product values match its related options.

        Case 1: values match.
        Case 2: values not match.
        """
        # Case 1.
        product = self.program_coupon_1.discount_line_product_id
        product.write({"sale_ok": True, "categ_id": False})
        self.product_category_coupon.program_option_ids = [
            (6, 0, (self.program_option_fixed_amount | self.program_option_sale_ok).ids)
        ]
        try:
            product.categ_id = self.product_category_coupon.id
        except UserError:
            self.fail("Must not raise when product matches option values.")
        # Case 2.
        with self.assertRaises(UserError):
            product.sale_ok = False

    def test_05_product_category_check_program_option_ids(self):
        """Validate if correct program options are set on category.

        Case 1: incorrect options per program type.
        Case 2: incorrect options per option type.
        """
        # Case 1.
        self.program_option_fixed_amount.program_type = "promotion_program"
        with self.assertRaises(UserError):
            self.product_category_coupon.program_option_ids = [
                (
                    6,
                    0,
                    (
                        self.program_option_fixed_amount | self.program_option_sale_ok
                    ).ids,
                )
            ]
        # Case 2.
        with self.assertRaises(UserError):
            self.product_category_coupon.program_option_ids = [
                (
                    6,
                    0,
                    (self.program_option_sale_ok | self.program_option_not_sale_ok).ids,
                )
            ]

    def test_06_product_category_check_program_option_ids(self):
        """Validate if correct program options are set on category.

        Case 1: incorrect options per program type.
        Case 2: incorrect options per option type.
        """
        # Case 1.
        self.program_option_fixed_amount.program_type = "promotion_program"
        with self.assertRaises(UserError):
            self.product_category_coupon.program_option_ids = [
                (
                    6,
                    0,
                    (
                        self.program_option_fixed_amount | self.program_option_sale_ok
                    ).ids,
                )
            ]
        # Case 2.
        with self.assertRaises(UserError):
            self.product_category_coupon.program_option_ids = [
                (
                    6,
                    0,
                    (self.program_option_sale_ok | self.program_option_not_sale_ok).ids,
                )
            ]

    def test_07_default_promotion_next_order_category(self):
        """Check if default category is set on next order type promo.

        Case 1: onchange with promo_applicability = on_current_order
        Case 2: onchange with promo_applicability = on_next_order
        Case 3: check if only one default categ can be used.
        """
        # Case 1.
        self.product_category_promotion.default_promotion_next_order_category = True
        program = self.SaleCouponProgram.create(
            {
                "name": "Promotion Program",
                "program_type": "promotion_program",
                "promo_applicability": "on_current_order",
                "reward_type": "discount",
                "discount_type": "fixed_amount",
                "discount_fixed_amount": 1000,
                "related_product_default_code": CODE_COUPON_PROGRAM,
                # Putting incorrect on purpose.
                "related_product_categ_id": self.product_category_coupon.id,
            }
        )
        program._onchange_promo_applicability()
        self.assertEqual(program.related_product_categ_id, self.product_category_coupon)
        # Case 2.
        program.promo_applicability = "on_next_order"
        program._onchange_promo_applicability()
        self.assertEqual(
            program.related_product_categ_id, self.product_category_promotion
        )
        # Case 3.
        with self.assertRaises(ValidationError):
            self.product_category_promotion.copy(
                default={"default_promotion_next_order_category": True}
            )

    def test_08_onchange_product_categ_with_opts(self):
        """Onchange product category that has program option."""
        product = self.program_coupon_1.discount_line_product_id
        self.assertFalse(product.sale_ok)
        self.product_category_coupon.program_option_ids = [
            (4, self.program_option_sale_ok.id)
        ]
        # Need to use Form, so constraint is not triggered before
        # onchange.
        with Form(product) as p:
            p.categ_id = self.product_category_coupon
            # product._onchange_product_categ_with_opts()
            self.assertTrue(p.sale_ok)
