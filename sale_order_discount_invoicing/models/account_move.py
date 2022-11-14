# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import copy

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains("line_ids")
    def _check_split_lines_constrains(self):
        """
        We want to be sure split lines are still both together
        and with same quantities.

        Considering couple of invoice lines with sale line links.
        """
        for move in self:
            split_lines = move.line_ids.filtered("is_split_line")
            for split_line in split_lines:
                sale_line_ids = split_line.sale_line_ids
                quantity = split_line.quantity
                other_split_lines = split_lines - split_line
                couple_split_line = other_split_lines.filtered(
                    lambda l: l.sale_line_ids == sale_line_ids
                )
                if not (
                    len(couple_split_line) == 1
                    and couple_split_line.quantity == quantity
                ):
                    raise ValidationError(
                        _(
                            "The line you have deleted/modified is linked to "
                            "another one in the Sale Order.\n"
                            "Please delete/modify both lines."
                        )
                    )

    def _can_process_discount_line_vals(self, invoice_line_vals):
        # To allow to override it in specific
        return True

    def _get_discount_line_values(
        self, invoice_line_vals, price_unit, origin_price_unit
    ):
        product_id = invoice_line_vals["product_id"]
        discount_line = invoice_line_vals.copy()
        product = self.env["product.product"].browse(product_id)
        discount_account = product.product_tmpl_id.get_product_accounts(
            fiscal_pos=self.fiscal_position_id
        )["discount"]
        discount_line.update(
            {
                "account_id": discount_account.id,
                "price_unit": price_unit - origin_price_unit,
                "name": _("Discount on %s") % discount_line["name"],
                "sale_line_ids": invoice_line_vals.get("sale_line_ids"),
                "is_split_line": True,
                "is_split_discount_line": True,
            }
        )
        return discount_line

    def _process_discount_line_vals(self, invoice_line_vals):
        """if the invoice line has a slashed price, split it in two, one for the full
        price and one for the discount. Otherwise keep it"""
        if "origin_price_unit" in invoice_line_vals:
            origin_price_unit = invoice_line_vals.pop("origin_price_unit")
            if not self._can_process_discount_line_vals(invoice_line_vals):
                yield invoice_line_vals
            else:
                price_unit = invoice_line_vals["price_unit"]
                invoice_line_vals["price_unit"] = origin_price_unit
                # FIXME use correct rounding
                precision_rounding = self.env.user.company_id.currency_id.rounding
                if 0 != float_compare(
                    origin_price_unit,
                    price_unit,
                    precision_rounding=precision_rounding,
                ):
                    invoice_line_vals["is_split_line"] = True
                    yield invoice_line_vals
                    discount_line = self._get_discount_line_values(
                        invoice_line_vals, price_unit, origin_price_unit
                    )
                    yield discount_line
                else:
                    yield invoice_line_vals
        else:
            yield invoice_line_vals

    @api.model
    def _move_autocomplete_invoice_lines_create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            if not vals.get("invoice_line_ids"):
                new_vals_list.append(vals)
                continue
            new_invoice_lines = []
            sequence = 0
            for cmd, _virtualid, line in vals["invoice_line_ids"]:
                # this method is normally code at account.move creation, so we
                # should really have the (0, virtualid, dict) instructions in
                # invoice_line_ids.
                assert cmd == 0, "special case found, code needs fixing"
                for line_vals in self._process_discount_line_vals(line):
                    sequence += 1
                    line_vals["sequence"] = sequence
                    new_invoice_lines.append((0, 0, line_vals))
            vals["invoice_line_ids"] = new_invoice_lines
            new_vals_list.append(vals)
        return super()._move_autocomplete_invoice_lines_create(new_vals_list)

    @api.model
    # Disable pylint because "Dangerous default value {} as argument"
    # but function signature provides from code core.
    def new(
        self, values={}, origin=None, ref=None
    ):  # pylint: disable=dangerous-default-value
        # flake8: noqa
        """
        OCA Module bank-payment/account_payment_partner override create(...)
        function and use a new(...) before call create(...) to update values.

        In our module,
        we add a non-existing field "origin_price_unit" into invoice line values.
        And we remove this field during
        the process of _move_autocomplete_invoice_lines_create(...).

        Problem is this function is not called when call new function.
        Then we need to remove "origin_price_unit" when calling new(...) function
        to avoid a failure when executing new(...) function
        """
        new_values = copy.deepcopy(values)
        if new_values.get("invoice_line_ids"):
            new_invoice_lines = []
            for cmd, _virtualid, line in new_values["invoice_line_ids"]:
                if cmd in [0, 1] and line and "origin_price_unit" in line:
                    # Comment from code core (write function of models.py)
                    # ``(0, 0, values)``
                    #     adds a new record created
                    #     from the provided ``value`` dict.
                    # ``(1, id, values)``
                    #     updates an existing record of id ``id`` with the
                    #     values in ``values``.
                    #     Can not be used in :meth:`~.create`.
                    # Other commands not contain values dict.
                    line.pop("origin_price_unit")
                new_invoice_lines.append((cmd, _virtualid, line))
        return super().new(values=new_values, origin=origin, ref=ref)
