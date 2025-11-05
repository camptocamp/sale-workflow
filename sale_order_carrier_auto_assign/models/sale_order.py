# Copyright 2020 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    carrier_id = fields.Many2one(
        compute="_compute_carrier_id", store=True, readonly=False
    )

    @api.depends("partner_id", "partner_shipping_id", "order_line.product_id", "state")
    @api.depends_context("override_carrier", "carrier_from_create")
    def _compute_carrier_id(self):
        """
        Automatically compute delivery carrier.

        Logic:
        - If 'override_carrier' is in context, we override the current carrier
        - If 'carrier_from_create' is in context,
          we only set the carrier on creation if enabled
        - Do not change carrier if order is confirmed (state 'sale')
        """
        preserve_carrier = not self.env.context.get("override_carrier")
        on_create = self.env.context.get("carrier_from_create")
        for order in self:
            if on_create and not order._is_auto_set_carrier_on_create():
                continue
            if order.state == "sale":
                continue
            order._set_delivery_carrier(preserve_order_carrier=preserve_carrier)

    def _is_auto_set_carrier_on_create(self):
        return (
            self.state in ("draft", "sent")
            and self.company_id.carrier_on_create
            and not self.is_all_service
        )

    @api.model_create_multi
    def create(self, vals_list):
        return super(SaleOrder, self.with_context(carrier_from_create=True)).create(
            vals_list
        )

    def write(self, vals):
        if self._is_auto_set_carrier_on_write(vals):
            self = self.with_context(override_carrier=True)
        return super().write(vals)

    def _is_auto_set_carrier_on_write(self, vals):
        return not vals.get("carrier_id") and (
            vals.get("partner_id") or vals.get("partner_shipping_id")
        )

    def _is_auto_set_carrier_on_confirm(self):
        return self.company_id.carrier_auto_assign and not self.is_all_service

    def action_confirm(self):
        for order in self:
            if order._is_auto_set_carrier_on_confirm():
                order._set_delivery_carrier(
                    set_delivery_line=True,
                    preserve_order_carrier=True,
                )
        return super().action_confirm()

    def _set_delivery_carrier(
        self, set_delivery_line=True, preserve_order_carrier=True
    ):
        """Automatically change delivery carrier.

        :param set_delivery_line: It will create or update the delivery line
        :param preserve_order_carrier: It will respect the carrier set on the order
        """
        for order in self:
            if (
                not order.order_line
                or isinstance(order.id, models.NewId)
                and not order._origin
            ):
                continue
            if order.delivery_set and preserve_order_carrier:
                continue
            delivery_wiz_action = order.action_open_delivery_wizard()
            delivery_wiz_context = delivery_wiz_action.get("context", {})
            if not delivery_wiz_context.get("default_carrier_id"):
                continue
            delivery_wiz_model = self.env[
                delivery_wiz_action.get("res_model")
            ].with_context(**delivery_wiz_context)
            if order._origin:
                # If `self._origin` is set, it can be a NewId object: use always its id
                delivery_wiz_model = delivery_wiz_model.with_context(
                    default_order_id=order._origin.id
                )
            delivery_wiz = delivery_wiz_model.new({})
            # Do not override carrier
            if preserve_order_carrier and order.carrier_id:
                delivery_wiz.carrier_id = order.carrier_id
            if not set_delivery_line or order.is_all_service:
                # Only set the carrier
                if order.carrier_id != delivery_wiz.carrier_id:
                    order.carrier_id = delivery_wiz.carrier_id
            else:
                delivery_wiz._get_delivery_rate()
                delivery_wiz.button_confirm()
