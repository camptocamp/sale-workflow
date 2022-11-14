# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common

QTY = 5


class TestSaleInvoiceDiscount(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.country_id = cls.env.ref("base.fr").id
        cls.setUpTaxAcc()
        cls.setUpClassicProducts()
        cls.setUpAdditionalAccounts()
        cls.setUpAccountJournal()

        # Create the SO with 1 order line
        cls.partner1 = cls.env["res.partner"].create(
            {
                "name": "partner_a",
                "company_id": False,
                "property_account_receivable_id": cls.property_account_receivable_id.id,
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        cls.sale_order1 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner1.id,
                "partner_invoice_id": cls.partner1.id,
                "partner_shipping_id": cls.partner1.id,
            }
        )
        SaleOrderLine = cls.env["sale.order.line"].with_context(tracking_disable=True)
        # cls.product_order_tax_included.taxes_id = cls.tax_price_include.id
        cls.sol_prod_order_1 = SaleOrderLine.create(
            {
                "name": cls.product_order_tax_included.name,
                "product_id": cls.product_order_tax_included.id,
                "product_uom_qty": QTY,
                "product_uom": cls.product_order_tax_included.uom_id.id,
                "price_unit": cls.product_order_tax_included.list_price,
                "origin_price_unit": 1000,
                "order_id": cls.sale_order1.id,
            }
        )
        cls.sale_order2 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner1.id,
                "partner_invoice_id": cls.partner1.id,
                "partner_shipping_id": cls.partner1.id,
            }
        )
        # cls.product_order_tax_excluded.taxes_id = cls.tax_price_exclude.id
        cls.sol_prod_order_2 = SaleOrderLine.create(
            {
                "name": cls.product_order_tax_excluded.name,
                "product_id": cls.product_order_tax_excluded.id,
                "product_uom_qty": QTY,
                "product_uom": cls.product_order_tax_excluded.uom_id.id,
                "price_unit": cls.product_order_tax_excluded.list_price,
                "origin_price_unit": 1000,
                "order_id": cls.sale_order2.id,
            }
        )

    @classmethod
    def setUpTaxAcc(cls):
        # Set up some taxes
        cls.tax_acc = cls.env["account.account"].create(
            {
                "code": "TVA",
                "name": "TWA",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
            }
        )

        cls.tax_price_include = cls.env["account.tax"].create(
            {
                "name": "8.5% incl",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 8.5,
                "price_include": True,
                "include_base_amount": False,
                "country_id": cls.env.ref("base.fr").id,
                "invoice_repartition_line_ids": [
                    (
                        0,
                        0,
                        {"factor_percent": 100, "repartition_type": "base"},
                    ),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100,
                            "repartition_type": "tax",
                            "account_id": cls.tax_acc.id,
                        },
                    ),
                ],
                "refund_repartition_line_ids": [
                    (
                        0,
                        0,
                        {"factor_percent": 100, "repartition_type": "base"},
                    ),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100,
                            "repartition_type": "tax",
                            "account_id": cls.tax_acc.id,
                        },
                    ),
                ],
            }
        )
        cls.tax_price_exclude = cls.env["account.tax"].create(
            {
                "name": "8.5% excl",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 8.5,
                "price_include": False,
                "include_base_amount": False,
                "country_id": cls.env.ref("base.fr").id,
                "invoice_repartition_line_ids": [
                    (
                        0,
                        0,
                        {"factor_percent": 100, "repartition_type": "base"},
                    ),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100,
                            "repartition_type": "tax",
                            "account_id": cls.tax_acc.id,
                        },
                    ),
                ],
                "refund_repartition_line_ids": [
                    (
                        0,
                        0,
                        {"factor_percent": 100, "repartition_type": "base"},
                    ),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100,
                            "repartition_type": "tax",
                            "account_id": cls.tax_acc.id,
                        },
                    ),
                ],
            }
        )

    @classmethod
    def setUpClassicProducts(cls):
        # Create an expense journal
        user_type_income = cls.env.ref("account.data_account_type_direct_costs")
        cls.account_income_product = cls.env["account.account"].create(
            {
                "code": "INCOME_PROD111",
                "name": "Income - Test Account",
                "user_type_id": user_type_income.id,
            }
        )
        cls.account_discount_product = cls.env["account.account"].create(
            {
                "code": "DISCOUNT_PROD111",
                "name": "Discount - Test Account",
                "user_type_id": user_type_income.id,
            }
        )
        # Create category
        cls.product_discount_category = cls.env["product.category"].create(
            {
                "name": "Product Category with Discount account",
                "property_account_income_categ_id": cls.account_income_product.id,
                "property_account_discount_categ_id": cls.account_discount_product.id,
            }
        )
        # Products
        uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_order_tax_excluded = cls.env["product.product"].create(
            {
                "name": "Product Test Excluded",
                "standard_price": 790.99,
                "list_price": 790.99,
                "type": "consu",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "invoice_policy": "order",
                "expense_policy": "no",
                "default_code": "PROD_ORDER_Excluded",
                "taxes_id": [(6, 0, [cls.tax_price_exclude.id])],
                "categ_id": cls.product_discount_category.id,
            }
        )
        cls.product_order_tax_included = cls.env["product.product"].create(
            {
                "name": "Product Test 1 Included",
                "standard_price": 790.99,
                "list_price": 790.99,
                "type": "consu",
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
                "invoice_policy": "order",
                "expense_policy": "no",
                "default_code": "PROD_ORDER_Included",
                "taxes_id": [(6, 0, [cls.tax_price_include.id])],
                "categ_id": cls.product_discount_category.id,
            }
        )

    @classmethod
    def setUpAdditionalAccounts(cls):
        """Set up some addionnal accounts: expenses, revenue, ..."""
        cls.property_account_receivable_id = cls.env["account.account"].create(
            {
                "code": "X2020",
                "name": "Test Receivable Account",
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        user_type_income = cls.env.ref("account.data_account_type_direct_costs")
        cls.account_income = cls.env["account.account"].create(
            {
                "code": "NC1112-1",
                "name": "Sale - Test Account",
                "user_type_id": user_type_income.id,
                "company_id": cls.company.id,
            }
        )
        user_type_revenue = cls.env.ref("account.data_account_type_revenue")
        cls.account_revenue = cls.env["account.account"].create(
            {
                "code": "NC1114-1",
                "name": "Sales - Test Sales Account",
                "user_type_id": user_type_revenue.id,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def setUpAccountJournal(cls):
        # Set up some journals
        cls.journal_sale_company = cls.env["account.journal"].create(
            {
                "name": "Sale Journal - Test",
                "code": "AJ-SALE",
                "type": "sale",
                "company_id": cls.company.id,
                "default_account_id": cls.account_income.id,
            }
        )

    def _test_result(self, expected, lines):
        for exp_line, move in zip(expected, lines):
            self.assertEqual(exp_line[0], move[0])
            self.assertAlmostEqual(exp_line[1], move[1], 1)
            self.assertAlmostEqual(exp_line[2], move[2], 1)

    def test_discount_invoicing_included_tax(self):
        """real price is 1000. we expect:

        Included tax:

        case:
        initial price = 1000
        unit price = 790.99
        TVA 8.5%

        Discount = 1000 - 790.99 = 209.01
        taxes
        - 209.01 = 192,64 * 8.5% = - 16.37
        1000 = 921,66 * 8.5% = 78.34
        78.34 - 16.37 = 61.97

        income
        1000 - 209.01 = 790.99
        209,01 - 16.37 = 192.64

        (*QTY)
        Account Debit Credit
        Product 0 921.66
        Discount 192.64 0
        Tax Product 0 78.34
        Tax Discount 16.37 0
        Income 790.99 0
        """

        self._confirm_so(self.sale_order1)
        invoice = self._create_invoice(self.sale_order1)
        move_lines = self._parse_move_lines(invoice)

        product_price = self.sale_order1.order_line.product_id.list_price
        origin_price_unit = self.sale_order1.order_line.origin_price_unit
        discount_amount = origin_price_unit - product_price

        tva_credit = origin_price_unit - (origin_price_unit / 1.085)
        tva_debit = discount_amount - (discount_amount / 1.085)
        total_tax = (tva_credit - tva_debit) * QTY
        net_income = (origin_price_unit - tva_credit) * QTY
        net_discount_expense = (discount_amount - tva_debit) * QTY

        expected = [
            ("Income - Test Account", 0.0, net_income),
            ("Discount - Test Account", net_discount_expense, 0.0),
            # separate records for taxes not created they posted on same line
            ("TWA", 0.0, total_tax),
            ("Test Receivable Account", product_price * QTY, 0.0),
        ]
        self._test_result(expected, move_lines)

    def test_discount_invoicing_excluded_tax(self):
        """real price is 1000. we expect:

        Excluded tax:

        case:
        initial price = 1000
        unit price = 790.99
        TVA 8.5%

        Discount = 1000 - 790.99 = 209.01
        taxes
        - 209.01 * 8.5% = - 17,77
        1000 * 8.5% = 85
        85 - 17,77 = 67,23

        Account Debit Credit
        Product 0 1000
        Discount 209,01 0
        Tax Product 0 85
        Tax Discount 17,76 0
        Income 858,22 0
        """

        self._confirm_so(self.sale_order2)
        invoice = self._create_invoice(self.sale_order2)
        move_lines = self._parse_move_lines(invoice)

        product_price = self.sale_order2.order_line.product_id.list_price
        origin_price_unit = self.sale_order2.order_line.origin_price_unit
        discount_amount = origin_price_unit - product_price

        tva_credit = origin_price_unit * (8.5 / 100)
        tva_debit = discount_amount * (8.5 / 100)
        total_tax = (tva_credit - tva_debit) * QTY
        net_income = origin_price_unit * QTY
        net_discount_expense = discount_amount * QTY
        receivable = (net_income - net_discount_expense) + total_tax

        expected = [
            ("Income - Test Account", 0.0, net_income),
            ("Discount - Test Account", net_discount_expense, 0.0),
            # separate records for taxes not created they posted on same line
            ("TWA", 0.0, total_tax),
            ("Test Receivable Account", receivable, 0.0),
        ]
        self._test_result(expected, move_lines)

    def _confirm_so(self, sale_order):
        # reset discount, prices, subtotal...
        for line in sale_order.order_line:
            line.product_id_change()

        sale_order.action_confirm()

    def _create_invoice(self, sale_order):
        payment = (
            self.env["sale.advance.payment.inv"]
            .with_context(
                **{
                    "active_model": "sale.order",
                    "active_ids": [sale_order.id],
                    "active_id": sale_order.id,
                    "default_journal_id": self.journal_sale_company.id,
                }
            )
            .create({"advance_payment_method": "delivered"})
        )
        payment.create_invoices()
        return sale_order.invoice_ids[0]

    def _parse_move_lines(self, invoice):
        move_lines = []
        for line in invoice.line_ids:
            move_lines.append((line.account_id.name, line.debit, line.credit))
        return move_lines
