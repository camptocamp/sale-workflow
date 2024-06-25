# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_pricelist_date(self):
        if self.env.context.get("force_pricelist_date"):
            return self.env.context["force_pricelist_date"]
        if self.pricelist_id.price_based_on_commitment_date and self.commitment_date:
            return self.commitment_date
        else:
            return False
