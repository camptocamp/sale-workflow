# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    archive_partner_product_sets = fields.Boolean(
        string="Archive product sets together with partner",
        config_parameter="sale_product_set.archive_partner_product_sets",
    )
