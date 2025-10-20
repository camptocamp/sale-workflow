# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from threading import current_thread

from odoo import api, exceptions, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    user_can_confirm = fields.Boolean(
        compute="_compute_user_can_confirm", compute_sudo=True
    )

    @api.depends("company_id.can_confirm_sales_groups_ids.users")
    @api.depends_context("uid")
    def _compute_user_can_confirm(self):
        user = self.env.user
        for company, sales in self.grouped("company_id").items():
            sales.user_can_confirm = user in company.can_confirm_sales_groups_ids.users

    def _skip_check_user_can_confirm(self) -> bool:
        """Checks whether the user permission to confirm should be checked

        If "skip_check_user_can_confirm" is found in the context, its value is returned.
        Returns True by default when in test mode, else False.
        """
        if "skip_check_user_can_confirm" in self.env.context:
            return bool(self.env.context["skip_check_user_can_confirm"])
        return bool(
            self.env.registry.in_test_mode()
            or getattr(current_thread(), "testing", False)
        )

    def action_confirm(self):
        # OVERRIDE: prevent users not in group "Can Confirm Sales" to confirm a sale
        # order, and raise a ``ValidationError`` instead
        if self._skip_check_user_can_confirm() or not self:
            return super().action_confirm()
        elif not all(self.mapped("user_can_confirm")):
            raise exceptions.ValidationError(
                self.env._("User %s cannot confirm Sale Orders", self.env.user.name)
            )
        return super().action_confirm()

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        # OVERRIDE: hide the SO ``action_confirm`` button to users not in group "Can
        # Confirm Sales"
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        if self._skip_check_user_can_confirm():
            return arch, view

        # We want to hide all the ``action_confirm()`` buttons related to ``sale.order``
        # records, so we find all of them, traverse their parent nodes top-down until
        # we reach the node's direct parent, and if we encounter fields along the way
        # (which can only be ``X2Many`` fields) we update the node's model, to make sure
        # we hide *only* the ``action_confirm()`` buttons related to ``sale.order``
        # records, not buttons with the same name for other models
        for node in arch.xpath("//button[@name='action_confirm']"):
            model = self.env["sale.order"]
            for fname in reversed([p.get("name") for p in node.iterancestors("field")]):
                model = self.env[model._fields[fname].comodel_name]
            if model._name == "sale.order":
                if value := node.get("invisible"):
                    node.set("invisible", f"not user_can_confirm or ({value})")
                else:
                    node.set("invisible", "not user_can_confirm")
        return arch, view
