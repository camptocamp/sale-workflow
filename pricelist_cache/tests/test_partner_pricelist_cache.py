# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.exceptions import UserError

from .common import LIST_PRICES_MAPPING, TestPricelistCacheCommon


@freeze_time("2021-03-15")
class TestPricelistCache(TestPricelistCacheCommon):
    def test_partner_pricelists(self):
        partner = self.partner
        for pricelist_xmlid, expected_result in LIST_PRICES_MAPPING.items():
            partner.property_product_pricelist = self.env.ref(pricelist_xmlid)
            price_list = partner._pricelist_cache_get_prices()
            # for test purposes, only test products referenced in demo data
            # Since cache is created for more or less products, depending
            # on the modules installed
            price_list = price_list.filtered(lambda p: p.product_id in self.products)
            result = [{"id": c.product_id.id, "price": c.price} for c in price_list]
            result.sort(key=lambda r: r["id"])
            self.assertEqual(result, expected_result)

    def _flush_cache(self):
        self.cache_model.flush_pricelist_cache()

    def test_partner_inconsistent_cache(self):
        # Initialize
        partner_pricelist = self.list3
        parent_pricelist = self.list2
        parent_pricelists = self.list2 | self.list1 | self.list0
        self.partner.property_product_pricelist = partner_pricelist
        self._flush_cache()
        self.assertFalse(self.partner.is_pricelist_cache_available)
        self.assertFalse(
            self.partner.property_product_pricelist.is_pricelist_cache_available
        )
        # Cache prices for the parents pricelists only
        self.cache_model.with_context(debug_test=True).update_product_pricelist_cache(
            pricelist_ids=parent_pricelists.ids
        )
        # Parent pricelists are cached
        self.assertTrue(
            all(
                pricelist.is_pricelist_cache_available
                for pricelist in parent_pricelists
            )
        )
        # But partner pricelist isn't
        self.assertFalse(partner_pricelist.is_pricelist_cache_available)
        # Therefore, trying to get prices for this partner should raise an exception
        regex = r"Pricelist caching in progress. Retry later"
        with self.assertRaisesRegex(UserError, regex):
            self.partner._pricelist_cache_get_prices()
        # However, if partner has list2 as a pricelist, prices are retrieved correctly
        # since list2 is the parent of list3
        self.partner.property_product_pricelist = parent_pricelist
        self.assertTrue(self.partner.is_pricelist_cache_available)
        # And retrieving prices do not raises an exception
        self.partner._pricelist_cache_get_prices()
        # Now, finish the caching
        self.cache_model.update_product_pricelist_cache(
            pricelist_ids=partner_pricelist.ids
        )
        self.partner.property_product_pricelist = partner_pricelist
        # Cache is avaiable for partner,
        # and retrieving prices doesn't raise an exception.
        self.assertTrue(self.partner.is_pricelist_cache_available)
        self.partner._pricelist_cache_get_prices()
