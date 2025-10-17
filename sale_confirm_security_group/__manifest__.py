# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

{
    "name": "Sale - Confirmation Security Group",
    "summary": "Adds security group and checks to allow only certain users to confirm"
    " sale orders",
    "version": "18.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA) ",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Sale",
    "license": "AGPL-3",
    "depends": ["sale"],
    "data": ["security/res_groups.xml"],
    "installable": True,
}
