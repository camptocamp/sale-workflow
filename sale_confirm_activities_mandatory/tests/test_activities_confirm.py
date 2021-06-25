# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.exceptions import UserError, AccessError
from odoo.addons.sale.tests import test_sale_common


class TestSaleActivitiesConfirm(test_sale_common.TestCommonSaleNoChart):

    @classmethod
    def setUpClass(cls):

        super(TestSaleActivitiesConfirm, cls).setUpClass()

        SaleOrder = cls.env['sale.order'].with_context(tracking_disable=True)

        model_so_id = cls.env['ir.model']._get('sale.order').id
        ActivityType = cls.env['mail.activity.type']
        cls.not_validation_step = ActivityType.create(
            {
                'category': 'default',
                'name': "Test1",
                "res_model_id": model_so_id
            }
        )
        cls.validation_step1 = ActivityType.create(
            {
                'category': 'validation',
                'name': "Test1 validation",
                "res_model_id": model_so_id
            }
        )
        cls.validation_step2 = ActivityType.create(
            {
                'category': 'validation',
                'name': "Test2 validation",
                "res_model_id": model_so_id,
                'force_next': True
            }
        )
        cls.validation_step2_1 = ActivityType.create(
            {
                'category': 'validation',
                'name': "Test2_1 validation",
                "res_model_id": model_so_id,
                "previous_type_ids": [(6, 0, [cls.validation_step2.id])],
            }
        )
        # link default_type for validation_step2 activity
        cls.validation_step2.default_next_type_id = cls.validation_step2_1.id

        cls.sale_order = SaleOrder.create({
            'partner_id': cls.partner_customer_usd.id,
            'partner_invoice_id': cls.partner_customer_usd.id,
            'partner_shipping_id': cls.partner_customer_usd.id,
            'pricelist_id': cls.pricelist_usd.id,
        })

        # create user to test validato_groups
        group_employee = cls.env.ref('base.group_user')
        Users = cls.env['res.users'].with_context(
            {'no_reset_password': True, 'mail_create_nosubscribe': True,
             'mail_create_nolog': True})
        cls.user_not_validator = Users.create({
            'name': 'Tyrion Lannister Employee',
            'login': 'tyrion',
            'email': 'tyrion@example.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [group_employee.id])],
        })
        account_values = {
            'property_account_payable_id': cls.account_payable.id,
            'property_account_receivable_id': cls.account_receivable.id,
        }
        cls.user_not_validator.partner_id.write(account_values)
        cls.group_salemanager = cls.env.ref('sales_team.group_sale_manager')
        cls.user_validator = Users.create({
            'name': 'Tyrion Lannister Manager',
            'login': 'tyrionM',
            'email': 'tyrionM@example.com',
            'notification_type': 'email',
            'groups_id': [
                (6, 0, [group_employee.id, cls.group_salemanager.id])],
        })
        cls.user_validator.partner_id.write(account_values)

    def test_steps01(self):
        # SO must have 3 activities (the default one and the 2 validations ones
        self.assertEqual(2, len(self.sale_order.activity_ids))
        self.assertNotIn(
            self.validation_step2_1.id,
            self.sale_order.mapped('activity_ids.activity_type_id').ids
        )
        with self.assertRaises(UserError):
            self.sale_order.action_confirm()

    def test_steps02(self):
        # mark steps as done and check we cannot confirm the SO because a new
        # activity has been generated for the SO
        for activity in self.sale_order.activity_ids:
            activity.action_done_schedule_next()
        # there should be only one activity now on the sale order
        self.assertEqual(1, len(self.sale_order.activity_ids))

        self.assertEqual(
            'validation',
            self.sale_order.activity_ids[0].activity_category
        )
        # Still cannot confirm sale order as there is one mandatory activity left
        with self.assertRaises(UserError):
            self.sale_order.action_confirm()
        # terminate the last activity
        self.sale_order.activity_ids[0].action_done_schedule_next()

        # no activities left on SO
        self.assertEqual(0, len(self.sale_order.activity_ids))
        # should be able to confirm sale order
        self.sale_order.action_confirm()
        self.assertIn(self.sale_order.state, ['sale', 'done'])

    def test_steps_acl(self):
        # assign a validator group to the last activity type
        self.validation_step2_1.validator_group_ids = self.group_salemanager
        # mark steps as done and check we cannot confirm the SO because a new
        # activity has been generated for the SO
        for activity in self.sale_order.activity_ids:
            activity.action_done_schedule_next()
        # there should be only one activity now on the sale order
        self.assertEqual(1, len(self.sale_order.activity_ids))

        self.assertEqual('validation',
                         self.sale_order.activity_ids[0].activity_category)
        # Still cannot confirm sale order as there is one mandatory activity left
        with self.assertRaises(UserError):
            self.sale_order.action_confirm()
        # error while terminating the last activity because of ACL
        with self.assertRaises(AccessError):
            self.sale_order.sudo(user=self.user_not_validator).activity_ids[
                0].action_done_schedule_next()

        self.sale_order.sudo(user=self.user_validator.id).activity_ids[
            0].action_done_schedule_next()
        # no activities left on SO
        self.assertEqual(0, len(self.sale_order.activity_ids))
        # user_not_validator should not be able to confirm sale order
        self.sale_order.sudo(user=self.user_validator.id).action_confirm()
        self.assertIn(self.sale_order.state, ['sale', 'done'])
