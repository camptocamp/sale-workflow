from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        res = super().write(vals)
        if "active" in vals:
            partner_product_sets = (
                self.env["product.set"]
                .with_context(active_test=False)
                .search([("partner_id", "=", self.id)])
            )
            partner_product_sets.sudo().write({"active": vals["active"]})
        return res
