# Copyright 2018 Okia SPRL
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLineCancel(models.TransientModel):
    _name = "sale.order.line.cancel"
    _description = "Cancel Remaining Wizard"

    def _get_sale_order_line(self):
        active_id = self._context.get("active_id")
        active_model = self._context.get("active_model")
        if not active_id or active_model != "sale.order.line":
            raise UserError(_("No sale order line ID found"))
        return self.env[active_model].browse(active_id)

    @api.model
    def _get_moves_to_cancel(self, line):
        return line.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))

    def cancel_remaining_qty(self):
        line = self._get_sale_order_line()
        if not line.can_cancel_remaining_qty:
            return False
        cancel_moves = self._get_moves_to_cancel(line)
        cancel_moves._action_cancel()
        line.order_id.message_post(
            body=_(
                "<b>%(product)s</b>: The order line has been canceled",
                product=line.product_id.display_name,
            )
        )
        return True
