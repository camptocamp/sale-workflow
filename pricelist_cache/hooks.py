# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists, create_column, table_exists

logger = logging.getLogger(__name__)


def set_default_partner_product_filter(env):
    """This hook is here because we couldn't set the default filter
    as a default value for partners.

    When the module is installed, Odoo creates the new field and at the
    same time tries to set the default value for all existing records in
    the DB. However the XML data (and thus 'product_filter_default' filter)
    is still not created at this stage.
    """
    partners_to_update = (
        env["res.partner"]
        .with_context(active_test=False)
        .search([("pricelist_cache_product_filter_id", "=", False)])
    )
    default_filter = env.ref("pricelist_cache.product_filter_default")
    partners_to_update.write({"pricelist_cache_product_filter_id": default_filter.id})


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    set_default_partner_product_filter(env)


def _set_is_pricelist_cache_computed(cursor):
    table_name = "product_pricelist"
    column_name = "is_pricelist_cache_computed"
    if column_exists(cursor, table_name, column_name):
        return
    logger.info(f"creating column {column_name} on table {table_name}")
    create_column(cursor, table_name, column_name, "boolean")
    query = f"""
        UPDATE {table_name}
        SET {column_name} = true;
    """
    cursor.execute(query)


def _set_is_pricelist_cache_available(cursor):
    table_name = "product_pricelist"
    column_name = "is_pricelist_cache_available"
    if column_exists(cursor, table_name, column_name):
        return
    logger.info(f"creating column {column_name} on table {table_name}")
    create_column(cursor, table_name, column_name, "boolean")
    query = f"""
        UPDATE {table_name}
        SET {column_name} = true;
    """
    cursor.execute(query)


def _set_parent_pricelist_ids(cursor):
    table_name = "product_pricelist_potato"
    if table_exists(cursor, table_name):
        return
    logger.info(f"creating table {table_name}")
    create_table_query = """
        CREATE TABLE product_pricelist_potato (
            child_id INTEGER NOT NULL,
            parent_id INTEGER NOT NULL,
            PRIMARY KEY(child_id, parent_id)
        );
        CREATE INDEX ON product_pricelist_potato (child_id, parent_id);
    """
    cursor.execute(create_table_query)
    fill_table_query = """
        INSERT INTO product_pricelist_potato (child_id, parent_id)
        SELECT DISTINCT ON (pricelist_id, base_pricelist_id)
            pricelist_id, base_pricelist_id
        FROM product_pricelist_item
        WHERE pricelist_id IS NOT NULL
        AND base_pricelist_id IS NOT NULL
        AND applied_on = '3_global'
        AND base = 'pricelist';
    """
    cursor.execute(fill_table_query)


def pre_init_hook(cursor):
    _set_is_pricelist_cache_available(cursor)
    _set_is_pricelist_cache_computed(cursor)
    _set_parent_pricelist_ids(cursor)
