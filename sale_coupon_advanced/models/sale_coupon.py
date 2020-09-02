# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    is_cumulative = fields.Boolean(string="None-cumulative Promotion")

    # Add possibility to use discount only on first order of a customer
    first_order_only = fields.Boolean(
        string="Apply only first",
        help="Apply only on the first order of each client matching the conditions",
    )

    first_n_orders_only = fields.Integer(
        help="Maximum number of sales orders of the customer in which reward \
         can be provided",
        string="Apply only on the next ",
        default=0,
    )

    @api.constrains("first_n_orders_only")
    def _constrains_first_n_orders_positive(self):
        for record in self:
            if record.first_order_only < 0:
                raise exceptions.ValidationError(
                    _("`Apply only on the next` should not be a negative value.")
                )

    def _get_order_count(self, order):
        return self.env["sale.order"].search_count(
            [
                ("partner_id", "=", order.partner_id.id),
                ("state", "!=", "cancel"),
                ("id", "!=", order.id),
            ]
        )

    def _check_promo_code(self, order, coupon_code):
        order_count = self._get_order_count(order)
        if self.first_order_only and order_count:
            return {"error": _("Coupon can be used only for the first sale order!")}
        if self.first_n_orders_only and order_count >= self.first_n_orders_only:
            return {
                "error": _(
                    "Coupon can be used only for the first %s sale order!"
                    % (str(self.first_n_orders_only))
                )
            }
        return super()._check_promo_code(order, coupon_code)

    def _filter_first_order_programs(self, order):
        """
        Filter programs where first_order_only is True,
        and the customer have already ordered before.
        """
        if self._get_order_count(order):
            return self.filtered(lambda program: not program.first_order_only)
        else:
            return self

    def _filter_n_first_order_programs(self, order):
        """
        Filter programs where first_n_orders_only is set, and
        the max number of orders have already been reached by the customer.
        """
        order_count = self._get_order_count(order)
        filtered_programs = self.env[self._name]
        for program in self:
            if (
                program.first_n_orders_only
                and order_count >= program.first_n_orders_only
            ):
                continue
            filtered_programs |= program
        return filtered_programs

    @api.model
    def _filter_programs_from_common_rules(self, order, next_order=False):
        """ Return the programs if every conditions is met
            :param bool next_order: is the reward given from a previous order
        """
        programs = super()._filter_programs_from_common_rules(order, next_order)
        programs = programs._filter_first_order_programs(order)
        programs = programs._filter_n_first_order_programs(order)
        return programs
