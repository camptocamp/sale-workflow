# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Sale Stock Line Customer Reference",
    "summary": (
        "Allow you to add a customer reference on order lines "
        "propataged to move operations."
    ),
    "version": "14.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Sales/Sales",
    "depends": ["sale_stock"],
    "data": [
        "views/sale_order.xml",
        "views/stock_move.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "development_status": "Beta",
}
