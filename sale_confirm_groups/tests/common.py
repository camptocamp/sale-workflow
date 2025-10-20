# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
from odoo.addons.sale.tests.common import TestSaleCommonBase


class TestSaleConfirmGroupsCommon(TestSaleCommonBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Update context env to force-test the user groups checks while testing
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                skip_check_user_can_confirm=False,
                **DISABLED_MAIL_CONTEXT,
            )
        )
        # Prepare 2 users, a sales user and a sales manager
        group_user = "sales_team.group_sale_salesman"
        group_manager = "sales_team.group_sale_manager"
        cls.user_with_group = new_test_user(
            cls.env,
            login="test-sale-user-with-confirm-group",
            groups=f"{group_user},{group_manager}",
        )
        cls.user_without_group = new_test_user(
            cls.env,
            login="test-sale-user-without-confirm-group",
            groups=f"{group_user}",
        )
        # Setup company
        cls.env.company.can_confirm_sales_groups_ids = cls.env.ref(group_manager)
