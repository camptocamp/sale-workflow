# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _is_commitment_date_a_public_holiday(self):
        """
        Returns True if commitment_date is a public holiday
        :return: bool
        """
        self.ensure_one()
        res = False
        if not self.commitment_date:
            return res
        commitment_date = fields.Datetime.context_timestamp(
            self, self.commitment_date
        ).date()
        holidays_filter = [("year", "=", commitment_date.year)]
        partner = self.partner_shipping_id or self.partner_id
        if partner:
            if partner.country_id:
                holidays_filter.append("|")
                holidays_filter.append(("country_id", "=", False))
                holidays_filter.append(("country_id", "=", partner.country_id.id))
            else:
                holidays_filter.append(("country_id", "=", False))
        pholidays = self.env["hr.holidays.public"].search(holidays_filter)
        if not pholidays:
            return res

        states_filter = [("year_id", "in", pholidays.ids)]
        if partner.state_id:
            states_filter += [
                "|",
                ("state_ids", "=", False),
                ("state_ids", "=", partner.state_id.id),
            ]
        else:
            states_filter.append(("state_ids", "=", False))
        states_filter.append(("date", "=", commitment_date))
        hhplo = self.env["hr.holidays.public.line"]
        holidays_line = hhplo.search(states_filter, limit=1)
        return bool(holidays_line)

    def check_commitment_date(self):
        """
        Returns True if the check is ok
        :return: bool
        """
        return not self._is_commitment_date_a_public_holiday()

    def _fields_trigger_check_exception(self):
        res = super()._fields_trigger_check_exception()
        res.append("commitment_date")
        return res
