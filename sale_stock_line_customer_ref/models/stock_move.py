# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    customer_ref = fields.Char(
        compute="_compute_customer_ref", readonly=True, store=True
    )

    @api.depends("sale_line_id.customer_ref", "move_dest_ids.sale_line_id")
    def _compute_customer_ref(self):
        for move in self:
            sale_line = move._get_related_sale_line()
            move.customer_ref = sale_line.customer_ref

    def _get_related_sale_line(self):
        """Return the SO line from the ship move (if any)."""
        self.ensure_one()
        if self.sale_line_id:
            return self.sale_line_id
        # Search in the destination moves recursively until we find a SO line
        moves_dest = self.move_dest_ids
        sale_line = self.sale_line_id.browse()
        for move_dest in moves_dest:
            if move_dest.sale_line_id:
                sale_line = move_dest.sale_line_id
                break
            sale_line = move_dest._get_related_sale_line()
            if sale_line:
                break
        return sale_line

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        # While ship moves can't be merged together as they are coming from
        # different SO lines ('sale_line_id' is part of the merge-key in
        # 'sale_stock'), we still want to avoid a merge of chained moves like
        # pick+pack.
        distinct_fields.append("customer_ref")
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super()._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.customer_ref)
        return keys_sorted
