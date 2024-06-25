# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Sale Order Carrier Auto Assign",
    "summary": "Auto assign delivery carrier on sale order confirmation",
    "version": "16.0.1.2.0",
    "category": "Operations/Inventory/Delivery",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "license": "AGPL-3",
    "data": ["views/res_config_settings_views.xml"],
    "application": False,
    "installable": True,
    "depends": ["delivery"],
}
