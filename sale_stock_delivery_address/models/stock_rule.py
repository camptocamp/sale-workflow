# Copyright 2020-22 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def run(self, procurements, raise_user_error=True):
        Procurement = self.env["stock.rule"].Procurement
        new_procs = []

        for proc in procurements:
            sale_line_id = proc.values.get("sale_line_id")
            if not sale_line_id:
                new_procs.append(proc)
                continue

            sale_line = self.env["sale.order.line"].browse(sale_line_id)
            procurement_values = dict(proc.values)

            if sale_line.dest_address_id:
                dest_partner = sale_line.dest_address_id
                procurement_values["partner_id"] = dest_partner.id
                new_location = dest_partner.property_stock_customer
            else:
                new_location = proc.location_id

            new_procs.append(
                Procurement(
                    proc.product_id,
                    proc.product_qty,
                    proc.product_uom,
                    new_location,
                    proc.name,
                    proc.origin,
                    proc.company_id,
                    procurement_values,
                )
            )

        return super().run(new_procs, raise_user_error)
