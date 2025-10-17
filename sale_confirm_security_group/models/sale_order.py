# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from threading import current_thread

from lxml import etree

from odoo import api, exceptions, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_groups_can_confirm_xmlids(self) -> list[str]:
        """Returns a list of groups that are allowed to confirm a SO

        Hook method, can be overridden by inheriting modules
        """
        return ["sale_confirm_security_group.group_can_confirm_sale"]

    @api.model
    def _user_can_confirm(self) -> bool:
        """Checks whether a user can confirm a SO

        Hook method, can be overridden by inheriting modules
        """
        return self.env.user.has_groups(",".join(self._get_groups_can_confirm_xmlids()))

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
        if self._skip_check_user_can_confirm() or self._user_can_confirm():
            return super().action_confirm()
        raise exceptions.ValidationError(self.env._("You cannot confirm a Sale Order"))

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        # OVERRIDE: hide the SO ``action_confirm`` button to users not in group "Can
        # Confirm Sales"
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if self._skip_check_user_can_confirm() or self._user_can_confirm():
            return result

        # We want to hide all the ``action_confirm()`` buttons related to ``sale.order``
        # records, so we find all of them, traverse their parent nodes top-down until
        # we reach the node's direct parent, and if we encounter fields along the way
        # (which can only be ``X2Many`` fields) we update the node's model, to make sure
        # we hide *only* the ``action_confirm()`` buttons related to ``sale.order``
        # records, not buttons with the same name for other models
        arch = etree.fromstring(result["arch"])
        for button_node in arch.xpath("//button[@name='action_confirm']"):
            current_model = self.env["sale.order"]
            for parent_node in reversed([n for n in button_node.iterancestors()]):
                if parent_node.tag == "field":
                    field = current_model._fields[parent_node.attrib["name"]]
                    current_model = self.env[field.comodel_name]
            if current_model._name == "sale.order":
                button_node.set("invisible", "1")
        result["arch"] = etree.tostring(arch)
        return result
