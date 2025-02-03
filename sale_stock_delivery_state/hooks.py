# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import math

from odoo.tools.misc import split_every

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    # Recompute '<sale.order>.delivery_status' by chunk to keep a constant
    # memory consumption
    order_model = env["sale.order"].with_context(prefetch_fields=False)
    rec_ids = order_model.search([]).ids
    _logger.info("Recompute 'delivery_status' on %s sale orders...", len(rec_ids))
    chunk_size = 2000
    nb_chunks = math.ceil(len(rec_ids) / chunk_size)
    for i, chunk_ids in enumerate(split_every(chunk_size, rec_ids), 1):
        _logger.info("... %s / %s", i, nb_chunks)
        records = order_model.browse(chunk_ids)
        records._compute_oca_delivery_status()
        env.cr.commit()
        env.invalidate_all()
