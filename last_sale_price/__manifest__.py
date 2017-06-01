# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Last Sale Price',
    'version': '10.0',
    'category': 'Sales',
    'description': '''
Last Sale Price
===============

Add price, quantity and date of a product of the last time it was sold to
a partner.

In order to let the salesman know if a customer already ordered a product.
And to give him hint about what price he should propose.
That information is shown next to the price in Sale Order's line Form.

Only Sale Orders' lines in state Confirmed and Done are considered to
compute those fields.

If multiple Sale Order lines for the same partner where made on the same
date for the same product, the sum of all quantity and the average price
will be displayed.
''',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'website': 'http://www.camptocamp.com/',
    'depends': ['base', 'sale'],
    'data': ['views/sale_view.xml'],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': "AGPL-3",
}