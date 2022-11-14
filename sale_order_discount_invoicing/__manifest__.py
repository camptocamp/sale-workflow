# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Discount Invoicing",
    "version": "15.0.1.0.0",
    "author": "Camptocamp SA, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Sales",
    "depends": [
        "account",
        "sale",
    ],
    "website": "https://github.com/OCA/sale-workflow",
    "data": [
        "views/sale_views.xml",
        "views/product_views.xml",
    ],
    "installable": True,
}
