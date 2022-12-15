# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import groupby


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_split_by_sale_line_id = fields.Many2one("sale.order.line", copy=False)
    is_split_line = fields.Boolean()
    is_split_discount_line = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._check_split_lines()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if {"move_id", "discount_split_by_sale_line_id", "quantity"}.intersection(vals):
            self._check_split_lines()
        return res

    def unlink(self):
        moves = self.move_id
        res = super().unlink()
        moves.line_ids.exists()._check_split_lines()
        return res

    def _check_split_lines(self):
        lines = self.filtered("discount_split_by_sale_line_id")
        if lines:
            groups = groupby(
                lines,
                key=lambda l: (
                    l.move_id.id,
                    l.discount_split_by_sale_line_id.id,
                    l.quantity,
                ),
            )
            if groups and any(len(recs) != 2 for key, recs in groups):
                raise ValidationError(
                    _(
                        "The lines you have created/deleted/modified are"
                        " linked some other ones in the Sale Order.\n"
                        "Please create/delete/modify both lines."
                    )
                )
