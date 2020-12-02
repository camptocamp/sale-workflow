from odoo import api, models

from .sale_coupon_program_option import DISCOUNT_PRODUCT_FNAME, SELF


class ProductProduct(models.Model):
    """Extend to force program name on related product."""

    _inherit = "product.product"

    def _handle_forced_product_vals(self, vals_list):
        forced_vals = self._context.get("forced_product_vals")
        if forced_vals:
            for vals in vals_list:
                vals.update(forced_vals)

    @api.onchange("categ_id")
    def _onchange_product_categ_with_opts(self):
        if self.categ_id._predicate_product_categ_with_opts():
            # Updating only product.product values here.
            options = self.categ_id.program_option_ids
            self.update(options.get_program_values()[DISCOUNT_PRODUCT_FNAME])

    @api.constrains("categ_id", "sale_ok")
    def _check_product_options(self):
        for rec in self:
            categ = rec.categ_id
            if categ._predicate_product_categ_with_opts():
                program = self.env["sale.coupon.program"].search(
                    [("discount_line_product_id", "=", rec.id)], limit=1
                )
                if program:
                    categ.program_option_ids.validate_program(
                        program, excluded_paths=[SELF]
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Extend to use forced program name if its passed."""
        self._handle_forced_product_vals(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        """Extend to use forced program name if its passed."""
        self._handle_forced_product_vals([vals])
        return super().write(vals)
