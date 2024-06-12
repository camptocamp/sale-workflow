# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from collections import OrderedDict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import AND
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    split_strategy_id = fields.Many2one("sale.order.split.strategy")

    def action_split(self):
        orders_without_split = self.filtered(lambda o: not o.split_strategy_id)
        if orders_without_split:
            raise UserError(
                _("Cannot split orders %s without any split strategy defined")
                % ", ".join(orders_without_split.mapped("name"))
            )
        new_order_ids = []
        for order in self:
            copy_sections = order.split_strategy_id.copy_sections
            copy_notes = order.split_strategy_id.copy_notes
            lines_to_split = order._select_lines_to_split()
            if not lines_to_split:
                raise UserError(
                    _(
                        "Cannot split order %s according to its strategy because there are no matching lines"
                    )
                    % order.name
                )
            new_order = order.copy(self._prepare_order_copy_defaults())
            # Prepare an OrderedDict from sale order lines and their sections
            sections_dict = OrderedDict()
            section_line_ids = None
            for line in order.order_line.sorted():
                if line.display_type == "line_section":
                    section_line_ids = sections_dict.setdefault(line.id, [])
                else:
                    if section_line_ids is None:
                        section_line_ids = sections_dict.setdefault(False, [])
                    section_line_ids.append(line.id)
            for section_id, line_ids in sections_dict.items():
                section_line = self.env["sale.order.line"].browse(section_id)
                section_lines = self.env["sale.order.line"].browse(line_ids)
                for line in section_lines:
                    if line in lines_to_split:
                        line.write(new_order._prepare_line_move_defaults())
                    # FIXME: We should consider if the line is part of the section
                    if copy_notes and line.display_type == "line_note":
                        line.copy(new_order._prepare_line_move_defaults())
                lines_in_section_to_split = [
                    li in lines_to_split for li in section_lines if not li.display_type
                ]
                # If all lines in section are to split, move the section to split order
                if copy_sections and section_line and all(lines_in_section_to_split):
                    section_line.write(new_order._prepare_line_move_defaults())
                # If any line in section is to split, copy the section to split order
                elif copy_sections and section_line and any(lines_in_section_to_split):
                    section_line.copy(new_order._prepare_line_move_defaults())
            order.message_post(body=order._prepare_message_split_to(new_order))
            new_order.message_post(body=new_order._prepare_message_split_from(order))
            new_order_ids.append(new_order.id)
        return self.browse(new_order_ids)

    def _prepare_message_split_from(self, order):
        self.ensure_one()
        template = self.env["ir.ui.view"].search(
            [("key", "=", "sale_order_split_strategy.split_from")], limit=1
        )
        if not template:
            return _(
                "This sale order was created after splitting lines from %s using strategy %s"
            ) % (order.name, order.split_strategy_id.name)
        else:
            return template._render(values={"from_order": order})

    def _prepare_message_split_to(self, order):
        self.ensure_one()
        template = self.env["ir.ui.view"].search(
            [("key", "=", "sale_order_split_strategy.split_to")], limit=1
        )
        if not template:
            return _(
                "This sale order had some of its lines split to %s using strategy %s"
            ) % (order.name, self.split_strategy_id.name)
        else:
            return template._render(values={"from_order": self, "to_order": order})

    @api.model
    def _prepare_order_copy_defaults(self):
        """Hook to customize values used on new sale order from split"""
        return {"order_line": False}

    def _prepare_line_move_defaults(self):
        """Hook to customize values used on new sale order line from split"""
        self.ensure_one()
        return {"order_id": self.id}

    def _select_lines_to_split(self):
        self.ensure_one()
        line_filter = self.split_strategy_id.line_filter_id
        domain = safe_eval(line_filter.domain)
        return self.env["sale.order.line"].search(
            AND([domain, [("order_id", "=", self.id)]])
        )
