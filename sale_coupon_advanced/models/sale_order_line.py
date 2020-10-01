# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderLine(models.Model):
    """Extend to add forced_reward_line field and override unlink."""

    _inherit = "sale.order.line"

    forced_reward_line = fields.Boolean(
        help="Tech field to cleanup automatically created lines"
    )

    def unlink(self):
        """Override to unlink disc lines when reward ones are unlinked.

        Also removes related sale.coupon.program records.
        """
        lines_to_remove = self.env['sale.order.line']
        SaleCouponProgram = self.env[
            'sale.coupon.program']
        for line in self:
            program = SaleCouponProgram.search([
                ('reward_type', '=', 'product'),
                ('reward_product_id', '=', line.product_id.id)
            ])
            if not program:
                continue
            order = line.order_id
            # Picking from related order, because it is possible to
            # remove order lines from different orders at once.
            order_lines = order.order_line
            lines_to_remove |= order_lines.filtered(
                lambda r: r.product_id == program.discount_line_product_id
            )
            order.no_code_promo_program_ids -= program
            order.code_promo_program_id -= program
        res = super(SaleOrderLine, self | lines_to_remove).unlink()
        return res
