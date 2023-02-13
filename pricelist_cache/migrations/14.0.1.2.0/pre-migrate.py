# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

_logger = logging.getLogger(__name__)


def lock_jobs(cr):
    query = """
        SELECT id
        FROM queue_job
        WHERE model_name = 'product.pricelist.cache'
        AND state NOT IN (
            'STARTED', 'DONE', 'CANCELLED', 'FAILED'
        )
        FOR UPDATE;
    """
    cr.execute(query)


def migrate(cr, version):
    _logger.error("Locking existing product.pricelist.cache jobs")
    lock_jobs(cr)
