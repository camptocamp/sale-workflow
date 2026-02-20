Website Sale Product Multiple Quantity
=======================================

This module extends the eCommerce flow to support **sales multiples**
(packaging quantities) directly on the product page.

When a product has a *Sales Multiple UoM* configured, the quantity entered
by the customer on the website is automatically rounded to a valid multiple
according to the interaction type.

The rounding logic is applied dynamically when the customer:

- Opens the product page
- Clicks the "+" (increase) button
- Clicks the "–" (decrease) button
- Manually enters a quantity

Rounding Rules
--------------

The behavior is designed to be human-friendly and predictable:

* On page load:
  The default quantity is rounded **UP** to the nearest multiple.

* When clicking "+":
  The quantity is rounded **UP** to the next valid multiple.

* When clicking "–":
  The quantity is rounded **DOWN** to the previous valid multiple.

* When manually entering a quantity:
  The value is rounded **UP** to the nearest valid multiple.

It is possible to set the quantity to ``0`` if the user decreases
the quantity below the first multiple.

Example
-------

If a product is sold in multiples of 500:

- Entering ``1`` → becomes ``500``
- Entering ``499`` → becomes ``500``
- Entering ``501`` → becomes ``1000``
- Clicking "–" from ``500`` → becomes ``0``
- Clicking "+" from ``0`` → becomes ``500``

It is the responsibility of the user to configure compatible Units of Measure.

The Sales Multiple UoM must belong to the same UoM category as the product's
sales UoM. Incorrect configuration (for example, mixing unrelated UoM
categories) may lead to unexpected quantity conversions and rounding results.

The module assumes that Units of Measure are properly defined and
conversion ratios are accurate.
