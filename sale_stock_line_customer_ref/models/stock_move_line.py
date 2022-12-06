# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    customer_ref = fields.Char(related="move_id.customer_ref", readonly=True)

    def write(self, vals):
        # TODO create a test for that
        # Overridden to store the 'customer_ref' on the destination package
        result_package_updated =  "result_package_id" in vals
        if result_package_updated:
            old_packages = self.result_package_id
        res = super().write(vals)
        if result_package_updated:
            # Remove Customer Ref. from packages that are used anymore
            new_package = self.result_package_id
            (old_packages - new_package).customer_ref = False
            # Collect all Customer Ref. from lines and store them in the package
            new_package.customer_ref = ", ".join(
                {x.customer_ref for x in self if x.customer_ref}
            )
        return res
