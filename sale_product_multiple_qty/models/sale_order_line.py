# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _round_sale_qty_to_multiple(self, qty_to_order: float) -> float:
        """Round the order line quantity to a multiple of the sales multiple UoM.

        :param qty_to_order: quantity expressed in the order line UoM (product_uom_id).
        :return: rounded quantity expressed in the order line UoM (product_uom_id).

        This method is inspired by
        ``stock.warehouse.orderpoint::_get_multiple_rounded_qty``.
        Round using "UP" strategy to the nearest multiple of
        product_id.sale_multiple_uom_id:

            - Convert qty_to_order from the product_uom_id to the
            product_id.sale_multiple_uom_id
            - Round the quantity using "UP" strategy
            - Convert back to the product_uom_id quantity

        Being said, if sales multiple UoM is divisible by the order line UoM,
        the result will be an integer.
        Otherwise, we expect rounding issues.
        It's up to the user to choose compatible UoMs.

        For example (compatible UoMs: 100 is divisible by 5):
            - order line UoM: Pack of 5 (5 units)
            - sales multiple UoM: Pack of 100 (100 units)
            - qty_to_order = 15 packs is rounded to 20 packs (100 units):
                15 packs of 5 = 75 units -> 1 pack of 100 = 100 units -> 20 packs of 5
            - qty_to_order = 55 packs is rounded to 60 packs (300 units):
                55 packs of 5 = 275 units -> 3 packs of 100 = 300 units -> 60 packs of 5

        For example (fractional result: 100 is not divisible by 6):
            - order line UoM: Pack of 6 (6 units)
            - sales multiple UoM: Pack of 100 (100 units)
            - qty_to_order = 13 packs is rounded to 17 packs (100.02 units):
                13 packs of 6 = 78 units -> 1.0 pack of 100 = 100 units
                -> 16.6667 packs of 6
        """
        self.ensure_one()
        packs = self.product_uom_id._compute_quantity(
            qty_to_order, self.product_id.sale_multiple_uom_id
        )
        packs = fields.Float.round(packs, precision_digits=0, rounding_method="UP")
        qty_rounded = self.product_id.sale_multiple_uom_id._compute_quantity(
            packs, self.product_uom_id
        )
        return qty_rounded

    def _nearest_valid_integer_qty(self, entered_qty: float) -> float:
        """Return the nearest valid integer qty bigger than entered (UP).

        The idea is simply to try integer quantities bigger than the entered
        quantity until we find one that, when rounded to the sales multiple UoM,
        gives an integer result.
        """
        self.ensure_one()
        qty_to_check = int(entered_qty) + 1
        while True:
            rounded_qty = self._round_sale_qty_to_multiple(qty_to_check)
            if rounded_qty.is_integer():
                return rounded_qty
            qty_to_check += 1

    def _prepare_incompatible_uom_warning_msg(
        self,
        entered_qty: float,
        rounded_qty: float,
    ) -> str:
        """Prepare the warning message for incompatible UoMs.

        :param entered_qty: quantity entered by the user.
        :param rounded_qty: rounded quantity to the sales multiple UoM.
        :return: warning message string.
        """
        self.ensure_one()
        multiple_uom = self.product_id.sale_multiple_uom_id
        valid_qty = self._nearest_valid_integer_qty(entered_qty)
        return self.env._(
            "Incompatible UoMs.\n"
            "The entered qty %(entered_qty).2f is rounded to "
            "%(rounded_qty).2f which is not valid "
            "for product '%(product)s'.\n"
            "It should be a multiple of %(multiple)s.\n"
            "The nearest valid qty is %(valid_qty).2f.",
            entered_qty=entered_qty,
            rounded_qty=rounded_qty,
            product=self.product_id.display_name,
            multiple=multiple_uom.display_name,
            valid_qty=valid_qty,
        )

    @api.onchange("product_id", "product_uom_qty", "product_uom_id")
    def _onchange_product_uom_qty(self):
        """Round product_uom_qty to a multiple of the sales multiple UoM.

        If sales multiple UoM is set on the product, this onchange rounds
        the order line quantity to the nearest multiple of that UoM using
        the "_round_sale_qty_to_multiple" method.

        If the rounded quantity is a floating point number, it means that the
        selected UoM is not compatible with the sales multiple UoM.
        See an example in the "_round_sale_qty_to_multiple" method.

        For such cases, a warning is displayed to inform the user
        about the incompatibility of UoMs.
        """
        for line in self:
            multiple_uom = line.product_id.sale_multiple_uom_id
            if not multiple_uom:
                continue

            qty_to_order = line.product_uom_qty or 0.0
            if qty_to_order <= 0:
                continue

            rounded_qty = line._round_sale_qty_to_multiple(qty_to_order)
            if not rounded_qty.is_integer():
                msg = line._prepare_incompatible_uom_warning_msg(
                    entered_qty=qty_to_order,
                    rounded_qty=rounded_qty,
                )
                return {"warning": {"title": self.env._("Warning"), "message": msg}}
            equal_qty = line.product_uom_id.compare(rounded_qty, qty_to_order) == 0
            if not equal_qty:
                line.product_uom_qty = rounded_qty

    @api.constrains(
        "product_id",
        "product_uom_qty",
        "product_uom_id",
    )
    def _check_rounded_sale_multiple_qty(self):
        """Ensure product_uom_qty is a multiple of the sales multiple UoM."""
        for line in self:
            multiple_uom = line.product_id.sale_multiple_uom_id
            if not multiple_uom:
                continue

            qty_to_order = line.product_uom_qty or 0.0
            if qty_to_order <= 0:
                continue

            rounded_qty = line._round_sale_qty_to_multiple(qty_to_order)
            if not rounded_qty.is_integer():
                msg = line._prepare_incompatible_uom_warning_msg(
                    entered_qty=qty_to_order,
                    rounded_qty=rounded_qty,
                )
                raise ValidationError(msg)
