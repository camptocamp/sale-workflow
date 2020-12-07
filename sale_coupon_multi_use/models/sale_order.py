from odoo import fields, models

ORDER_CTX_KEY = "coupon_sale_order"


def _get_order_line_coupons_filter(line):
    return lambda r: r.program_id.discount_line_product_id == line.product_id


class SaleOrder(models.Model):
    """Extend to modify action_confirm for multi-use coupons."""

    _inherit = "sale.order"

    coupon_multi_use_ids = fields.Many2many(
        "sale.coupon",
        "sale_order_coupon_multi_rel",
        "sale_id",
        "coupon_id",
        string="Multi Use Coupons",
        copy=False,
        readonly=True,
    )

    def _get_multi_use_coupons(self):
        self.ensure_one()
        # NOTE. This method must be called with ORDER_CTX_KEY on order.
        return self.coupon_multi_use_ids - self.applied_coupon_ids

    def action_confirm(self):
        """Extend to pass coupon_sale_order context."""
        for order in self:
            # Mimic same behavior as for single-user coupon.
            order = order.with_context(**{ORDER_CTX_KEY: order})
            super(SaleOrder, order).action_confirm()
            order._get_multi_use_coupons().consume_coupons()
        return True

    def action_cancel(self):
        """Extend to pass coupon_sale_order context."""
        for order in self:
            order = order = order.with_context(**{ORDER_CTX_KEY: order})
            super(SaleOrder, order).action_cancel()
            order._get_multi_use_coupons().reset_coupons()
            # Mimic applied_coupon_ids logic.
            order.coupon_multi_use_ids = [(5,)]
        return True

    def _get_coupons_from_2many_commands(self, commands):
        """Browse coupon IDs from 2many command."""
        ids = []
        for cmd in commands:
            if cmd[0] == 6:
                ids.extend(cmd[2])
            elif cmd[0] == 4:
                ids.append(cmd[1])
        return self.env["sale.coupon"].browse(ids)

    def _get_multi_use_coupons_from_2many_commands(self, commands):
        coupons = self._get_coupons_from_2many_commands(commands)
        return coupons.filtered("multi_use")

    def write(self, vals):
        """Extend to add multi-use coupons."""
        if vals.get("applied_coupon_ids"):
            # We want to add multi-use coupons that were added on
            # standard applied_coupon_ids, so such coupon is preserved (
            # applied_coupon_ids relation is removed once same coupon is
            # used on multiple sale orders).
            coupons_multi_use = self._get_multi_use_coupons_from_2many_commands(
                vals["applied_coupon_ids"]
            )
            if coupons_multi_use:
                vals["coupon_multi_use_ids"] = [(6, 0, coupons_multi_use.ids)]
        return super().write(vals)


class SaleOrderLine(models.Model):
    """Extend to reverse relate with consumption line."""

    _inherit = "sale.order.line"

    def unlink(self):
        """Extend to reactivate/reset removed multi-use coupons."""
        related_program_lines = self.env["sale.order.line"]
        # Reactivate coupons related to unlinked reward line
        for line in self.filtered(lambda line: line.is_reward_line):
            order = line.order_id
            _filter = _get_order_line_coupons_filter(line)
            coupons_to_detach = order.coupon_multi_use_ids.filtered(_filter)
            # We can only reactivate coupons that are not part of
            # applied_coupon_ids, because that part will signal
            # reactivate too.
            coupons_to_reactivate = (
                coupons_to_detach - order.applied_coupon_ids.filtered(_filter)
            )
            coupons_to_reactivate.write({"state": "new"})
            order.coupon_multi_use_ids -= coupons_to_detach
            # Remove the program from the order if the deleted line is
            # the reward line of the program.
            # And delete the other lines from this program (It's the
            # case when discount is split per different taxes)
            related_program = self.env["sale.coupon.program"].search(
                [("discount_line_product_id", "=", line.product_id.id)]
            )
            if related_program:
                # No need to remove promotions, because multi-use
                # coupons are not related with promotions.
                related_program_lines |= (
                    order.order_line.filtered(
                        lambda l: l.product_id
                        == related_program.discount_line_product_id
                    )
                    - line
                )
        return super(SaleOrderLine, self | related_program_lines).unlink()
