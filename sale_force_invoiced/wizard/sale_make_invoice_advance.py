# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import _, models
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _check_sale_orders_fully_invoiced(
        self,
    ):
        for sale_order in self.sale_order_ids:
            if sale_order.invoice_status == "invoiced":
                raise UserError(
                    _(
                        "Your order %s is blocked for invoicing. "
                        "You should modify the `Force Invoiced` status on your "
                        "sales order to unlock it."
                    )
                    % (sale_order.name)
                )

    def create_invoices(self):
        self._check_sale_orders_fully_invoiced()
        return super().create_invoices()
