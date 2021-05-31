# Copyright 2014 Carlos Sánchez Cifuentes <csanchez@grupovermon.com>
# Copyright 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2015 Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _recalculate_prices_get_fields(self):
        return ["price_unit"]

    def _reset_prices_get_fields(self):
        return ["discount"]

    def recalculate_prices(self):
        for line in self.mapped("order_line"):
            vals = line._convert_to_write(line.read()[0])
            if "product_tmpl_id" in line._fields:
                vals["product_tmpl_id"] = line.product_tmpl_id
            line2 = self.env["sale.order.line"].new(vals)
            fields_to_reset = self._reset_prices_get_fields()
            fields_to_write = self._recalculate_prices_get_fields() + fields_to_reset
            for field in fields_to_write:
                vals.pop(field)
            # Use onchange_helper
            result = line2.play_onchanges(vals, vals.keys())
            vals = {}
            for field in fields_to_write:
                if field in result:
                    vals.update({field: result.get(field)})
                elif field in fields_to_reset:
                    vals.update({field: 0.0})

            if vals:
                line.write(vals)
        return True

    def recalculate_names(self):
        for line in self.mapped("order_line").filtered("product_id"):
            # we make this to isolate changed values:
            line2 = self.env["sale.order.line"].new({"product_id": line.product_id})
            line2.product_id_change()
            line.name = line2.name
        return True
