# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleGlobalDiscount(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env.ref("base_global_discount.group_global_discount").write(
            {"users": [(4, cls.env.user.id)]}
        )
        cls.main_company = cls.env.ref("base.main_company")
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test account Global Discount",
                "code": "TEST99999",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.global_discount_obj = cls.env["global.discount"]
        cls.global_discount_1 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 1",
                "sequence": 1,
                "discount_scope": "sale",
                "discount": 20,
                "account_id": cls.account.id,
            }
        )
        cls.global_discount_2 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 2",
                "sequence": 2,
                "discount_scope": "sale",
                "discount": 30,
                "account_id": cls.account.id,
            }
        )
        cls.global_discount_3 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 3",
                "sequence": 3,
                "discount_scope": "sale",
                "discount": 50,
                "account_id": cls.account.id,
            }
        )
        cls.pricelist = cls.env.ref("product.list0")
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Mrs. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.partner_2.customer_global_discount_ids = (
            cls.global_discount_2 + cls.global_discount_3
        )
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test Product 1", "type": "service"}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "type": "service"}
        )
        cls.tax_group_5pc = cls.env["account.tax.group"].create(
            {"name": "Test Tax Group 5%", "sequence": 1}
        )
        cls.tax_group_15pc = cls.env["account.tax.group"].create(
            {"name": "Test Tax Group 15%", "sequence": 2}
        )
        cls.tax_1 = cls.tax_sale_a
        cls.tax_1.amount = 15.0
        cls.tax_2 = cls.tax_sale_b
        cls.tax_2.amount = 5.0
        cls.sale_journal0 = cls.env["account.journal"].create(
            {
                "name": "Sale Journal",
                "type": "sale",
                "code": "SJT0",
            }
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner_1
        with sale_form.order_line.new() as order_line:
            order_line.product_id = cls.product_1
            order_line.tax_id.clear()
            order_line.tax_id.add(cls.tax_1)
            order_line.tax_id.add(cls.tax_2)
            order_line.product_uom_qty = 2
            order_line.price_unit = 75
        with sale_form.order_line.new() as order_line:
            order_line.product_id = cls.product_2
            order_line.tax_id.clear()
            order_line.tax_id.add(cls.tax_1)
            order_line.tax_id.add(cls.tax_2)
            order_line.product_uom_qty = 3
            order_line.price_unit = 33.33
        cls.sale = sale_form.save()

    def get_taxes_widget_total_tax(self, order):
        return sum(
            tax_vals["tax_group_amount"]
            for tax_vals in order.tax_totals["groups_by_subtotal"]["Untaxed Amount"]
        )

    def test_01_global_sale_succesive_discounts(self):
        """Add global discounts to the sale order"""
        self.assertAlmostEqual(self.sale.amount_total, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 50)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        self.assertAlmostEqual(self.sale.amount_untaxed, 249.99)
        # Apply a single 20% global discount
        self.sale.global_discount_ids = self.global_discount_1
        # Discount is computed over the base and global taxes are computed
        # according to it line by line with the core method
        self.assertAlmostEqual(self.sale.amount_global_discount, 50)
        self.assertAlmostEqual(self.sale.amount_untaxed, 199.99)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_total, 239.99)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 40)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        # Apply an additional 30% global discount
        self.sale.global_discount_ids += self.global_discount_2
        self.assertAlmostEqual(self.sale.amount_global_discount, 110)
        self.assertAlmostEqual(self.sale.amount_untaxed, 139.99)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_total, 167.99)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 28)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        # The account move should look like this
        #   credit    debit  name
        # ========  =======  ===============================================
        #      150        0  Test Product 1
        #    99.99        0  Test Product 2
        #    13.13        0  Test TAX 15%
        #     4.38        0  TAX 5%
        #        0   105.01
        #        0       75  Test Discount 2 (30.00%) - Test TAX 15%, TAX 5%
        #        0    87.49  Test Discount 3 (50.00%) - Test TAX 15%, TAX 5%
        # ========  =======  ===============================================

    def test_02_global_sale_discounts_from_partner(self):
        """Change the partner and his global discounts go to the invoice"""
        # (30% then 50%)
        self.sale.partner_id = self.partner_2
        self.sale.onchange_partner_id_set_gbl_disc()
        self.assertAlmostEqual(self.sale.amount_global_discount, 162.49)
        self.assertAlmostEqual(self.sale.amount_untaxed, 87.5)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_total, 105.01)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 17.51)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )

    def test_03_global_sale_discounts_to_invoice(self):
        """All the discounts go to the invoice"""
        self.sale.partner_id = self.partner_2
        self.sale.onchange_partner_id_set_gbl_disc()
        self.sale.order_line.mapped("product_id").write({"invoice_policy": "order"})
        self.sale.action_confirm()
        move = self.sale._create_invoices()
        # Check the invoice relevant fields
        self.assertEqual(len(move.invoice_global_discount_ids), 2)
        discount_amount = sum(
            move.invoice_global_discount_ids.mapped("discount_amount")
        )
        self.assertAlmostEqual(discount_amount, 162.49)
        self.assertAlmostEqual(move.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(move.amount_untaxed, 87.5)
        self.assertAlmostEqual(move.amount_total, 105.01)
        # Expected Journal Entry
        # credit    debit    account
        # ========  =======  =========
        #      150        0  400000 (line 1)
        #    99.99        0  400000 (line 2)
        #    13.13        0  400000 (line_tax_1)
        #     4.38        0  400000 (line_tax_2)
        #        0   105.01  121000 (Base)
        #        0       75  TEST99999 (Global discount 1)
        #        0    87.49  TEST99999 (Global discount 2)
        #   267.50   267.50  <- Balance
        line_tax_1 = move.line_ids.filtered(lambda x: x.tax_line_id == self.tax_1)
        line_tax_2 = move.line_ids.filtered(lambda x: x.tax_line_id == self.tax_2)
        self.assertAlmostEqual(line_tax_1.credit, 13.13)
        self.assertAlmostEqual(line_tax_2.credit, 4.38)
        term_line = move.line_ids.filtered(
            lambda x: x.account_id.account_type == "asset_receivable"
        )
        self.assertAlmostEqual(term_line.debit, 105.01)
        discount_lines = move.line_ids.filtered("invoice_global_discount_id")
        self.assertEqual(len(discount_lines), 2)
        self.assertAlmostEqual(sum(discount_lines.mapped("debit")), 162.49)

    def test_04_incompatible_taxes(self):
        # Line 1 with tax 1 and tax 2
        # Line 2 with only tax 2
        self.sale.order_line[1].tax_id = [(6, 0, self.tax_1.ids)]
        with self.assertRaises(exceptions.UserError):
            self.sale.global_discount_ids = self.global_discount_1
            self.sale._compute_amounts()

    def test_05_no_taxes(self):
        self.sale.order_line[1].tax_id = False
        with self.assertRaises(exceptions.UserError):
            self.sale.global_discount_ids = self.global_discount_1
            self.sale._compute_amounts()

    def test_06_discounted_line(self):
        self.sale.global_discount_ids = self.global_discount_1
        line = self.sale.order_line[0]
        line.discount = 10
        self.assertAlmostEqual(line.price_subtotal, 135)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 234.99)
        self.assertAlmostEqual(self.sale.amount_untaxed, 187.99)

    def test_07_discount_line_with_fixed_taxes(self):
        # Create a fixed tax and apply on lines
        fixed_tax = self.safe_copy(self.company_data["default_tax_sale"])
        fixed_tax.write(
            {
                "amount": 5.0,
                "amount_type": "fixed",
            }
        )
        lines = self.sale.order_line
        lines.tax_id = [(6, 0, (fixed_tax + self.tax_1 + self.tax_2).ids)]
        # Based on test_01
        # 299.99 + (5 * 2) + (5 * 3)
        self.assertAlmostEqual(self.sale.amount_total, 324.99)
        # Based on test_01
        # 60 + (5 * 2) + (5 * 3)
        self.assertAlmostEqual(self.sale.amount_tax, 75)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        self.assertAlmostEqual(self.sale.amount_untaxed, 249.99)
        # Apply a single 20% global discount
        self.sale.global_discount_ids = self.global_discount_1
        # Discount is computed over the base and global taxes are computed
        # according to it line by line with the core method
        self.assertAlmostEqual(self.sale.amount_global_discount, 50)
        # Based on test_01
        # 40 + (5 * 2) + (5 * 3)
        self.assertAlmostEqual(self.sale.amount_tax, 65.0)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_untaxed, 199.99)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 324.99)
        self.assertAlmostEqual(self.sale.amount_total, 264.99)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )

    def test_08_global_discount_w_included_tax(self):
        """
        In case tax is configured as included-in-price,
        amount_tax should be calculated based on discounted amount
        """
        self.tax_1.price_include = True
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner_1
        with sale_form.order_line.new() as order_line:
            order_line.product_id = self.product_1
            order_line.tax_id.clear()
            order_line.tax_id.add(self.tax_1)
            order_line.product_uom_qty = 2
            order_line.price_unit = 75
        test_sale = sale_form.save()
        self.assertAlmostEqual(test_sale.amount_untaxed, 130.43)
        self.assertAlmostEqual(test_sale.amount_tax, 19.57)
        self.assertAlmostEqual(test_sale.amount_total, 150)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(test_sale), test_sale.amount_tax
        )
        # Apply a single 20% global discount
        test_sale.global_discount_ids = self.global_discount_1
        self.assertAlmostEqual(test_sale.amount_untaxed_before_global_discounts, 130.43)
        self.assertAlmostEqual(test_sale.amount_total_before_global_discounts, 150)
        self.assertAlmostEqual(test_sale.amount_global_discount, 26.09)
        self.assertAlmostEqual(test_sale.amount_untaxed, 104.34)
        # amount_tax is calculated based on discounted amount
        self.assertAlmostEqual(test_sale.amount_tax, 15.65)
        self.assertAlmostEqual(test_sale.amount_total, 119.99)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(test_sale), test_sale.amount_tax
        )
