As it causes problems in other module's tests when creating pricelist items,
and since the `base_automation` module won't be accessible in odoo community edition
anymore (since 17.0), we drop the base automation record in favor of a hook in
`product.pricelist.cache.create()`.
