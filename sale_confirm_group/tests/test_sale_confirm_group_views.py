# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from lxml.etree import fromstring
from odoo_test_helper import FakeModelLoader

from odoo import tools

from .common import TestSaleConfirmGroupCommon


class TestSaleConfirmGroupViews(TestSaleConfirmGroupCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Update context env to be able to use the view we'll create in tests
        cls.env = cls.env(context=dict(cls.env.context, load_all_views=True))

        # For button-invisibility testing we add:
        # - a dummy M2M field from ``sale.order`` to itself
        # - a dummy M2M field from ``sale.order`` to ``res.users`` and its inverse
        # - a dummy function ``action_confirm()`` on ``res.users``
        # so we can add nested list views w/ other ``action_confirm`` buttons
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import res_users, sale_order

        cls.loader.update_registry((sale_order.SaleOrder, res_users.ResUsers))

        # Load demo views
        tools.convert.convert_file(
            cls.env,
            module="sale_confirm_group",
            filename="demo/sale_order_test_views.xml",
            idref={},
            kind="test",
        )
        cls.sale_form = cls.env.ref("sale_confirm_group.dummy_sale_form_view")

    def test_action_confirm_invisible(self):
        arch = fromstring(self.env["sale.order"].get_view(self.sale_form.id)["arch"])
        # Buttons related to ``sale.order.action_confirm()``
        self.assertEqual(
            arch.xpath("//button[@id='test_button_1']")[0].get("invisible"),
            "not user_can_confirm",
        )
        self.assertEqual(
            arch.xpath("//button[@id='test_button_2']")[0].get("invisible"),
            "not user_can_confirm or (not id)",
        )
        self.assertEqual(
            arch.xpath("//button[@id='test_button_3']")[0].get("invisible"),
            "not user_can_confirm",
        )
        self.assertEqual(
            arch.xpath("//button[@id='test_button_4']")[0].get("invisible"),
            "not user_can_confirm or (not id)",
        )
        # Buttons related to ``res.users.action_confirm()``
        self.assertEqual(
            arch.xpath("//button[@id='test_button_5']")[0].get("invisible"), None
        )
        self.assertEqual(
            arch.xpath("//button[@id='test_button_6']")[0].get("invisible"), "not id"
        )
        self.assertEqual(
            arch.xpath("//button[@id='test_button_7']")[0].get("invisible"), None
        )
        self.assertEqual(
            arch.xpath("//button[@id='test_button_8']")[0].get("invisible"), "not id"
        )
