# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from .sale_coupon_program_option import DISCOUNT_PRODUCT_FNAME, SELF

# If related fields for product uses this prefix, init value will be
# automatically passed on related product.
PRODUCT_FNAME_PREFIX = "related_product_"
# NOTE. Need to copy/paste dependencies, because in standard Odoo these
# are buried inside write method (not reachable).
PRODUCT_NAME_DEPS = [
    "reward_type",
    "reward_product_id",
    "discount_type",
    "discount_percentage",
    "discount_apply_on",
    "discount_specific_product_ids",
    "discount_fixed_amount",
]


class SaleCouponProgram(models.Model):
    """Extend to improve product related product management."""

    _inherit = "sale.coupon.program"

    related_product_default_code = fields.Char(
        related="discount_line_product_id.default_code", readonly=False
    )
    related_product_categ_id = fields.Many2one(
        # Storing so constraint would not complain.
        related="discount_line_product_id.categ_id",
        readonly=False,
        store=True,
    )

    @api.onchange("related_product_categ_id")
    def _onchange_related_product_categ_id(self):
        categ = self.related_product_categ_id
        if categ._predicate_product_categ_with_opts():
            # Updating only sale.coupon.program values here.
            self.update(categ.program_option_ids.get_program_values()[SELF])

    @api.onchange("promo_applicability")
    def _onchange_promo_applicability(self):
        if (
            self.program_type == "promotion_program"
            and self.promo_applicability == "on_next_order"
        ):
            default_categ = self.env["product.category"].search(
                [("default_promotion_next_order_category", "=", True)], limit=1
            )
            if default_categ:
                self.related_product_categ_id = default_categ.id

    @api.constrains("related_product_categ_id", "reward_type", "discount_type")
    def _check_program_options(self):
        for rec in self:
            categ = rec.related_product_categ_id
            if categ._predicate_product_categ_with_opts():
                categ.program_option_ids.validate_program(
                    rec, excluded_paths=[DISCOUNT_PRODUCT_FNAME]
                )

    def _get_reward_line_product_extra_create_vals(self, vals):
        self.ensure_one()
        extra_vals = {}
        for fname, val in vals.items():
            # Only care about related product truthy vals.
            if fname.startswith(PRODUCT_FNAME_PREFIX) and val:
                # Remove prefix.
                product_fname = fname[len(PRODUCT_FNAME_PREFIX) :]
                extra_vals[product_fname] = val
        return extra_vals

    def _prepare_forced_product_vals(self):
        self.ensure_one()
        forced_product_vals = {"name": self.name}
        categ = self.related_product_categ_id
        if categ._predicate_product_categ_with_opts():
            options = categ.program_option_ids
            extra_product_vals = options.get_program_values(program=self)[
                DISCOUNT_PRODUCT_FNAME
            ]
            forced_product_vals.update(extra_product_vals)
        return forced_product_vals

    @api.model
    def create(self, vals):
        """Extend to initially update related product values.

        Related fields on product won't be updated by default, because
        product is created after related program creation.
        """
        # Using virtual record here, so we can pass product values when
        # product is created (this avoids multiple product update calls).
        program_new = self.new(values=vals)
        product_extra_vals = program_new._get_reward_line_product_extra_create_vals(
            vals
        )
        self = self.with_context(
            forced_product_vals=dict(
                product_extra_vals, **program_new._prepare_forced_product_vals()
            )
        )
        return super(SaleCouponProgram, self).create(vals)

    def write(self, vals):
        """Extend to update force update product name from program name.

        Name can be updated via forced_product_vals context, when
        product update is triggered by original implementation, or can
        be forced updated directly, when those dependencies are not
        changed.
        """
        for rec in self:
            name = vals.get("name") or rec.name
            rec = rec.with_context(forced_product_vals={"name": name})
            product_update = any(field in PRODUCT_NAME_DEPS for field in vals)
            super(SaleCouponProgram, rec).write(vals)
            # Directly update only if it was not updated from original
            # implementation already.
            if not product_update:
                rec.discount_line_product_id.name = name
        return True  # expected write return val.
