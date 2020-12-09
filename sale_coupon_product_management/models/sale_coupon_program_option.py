import operator

from odoo import _, api, fields, models
from odoo.exceptions import UserError

SELF = "__SELF__"
DISCOUNT_PRODUCT_FNAME = "discount_line_product_id"


class SaleCouponProgramOption(models.Model):
    """Model to hold specific information about coupon program opts.

    Option can define for example that Fixed Amount Discount must be
    used.
    """

    _name = "sale.coupon.program.option"
    _description = "Coupon/Promotion Option"

    def _get_option_type_selection(self):
        cfg = self._get_program_values_cfg()
        return [(k, v["label"]) for k, v in cfg.items()]

    def _get_program_type_selection(self):
        SCP = self.env["sale.coupon.program"]
        return SCP._fields["program_type"].selection

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    # Code to identify what option supposed to do.
    option_type = fields.Selection(_get_option_type_selection, required=True)
    # Used to to filter options per program type.
    program_type = fields.Selection(_get_program_type_selection, required=True)

    _sql_constraints = [
        (
            "option_type_uniq",
            "unique (option_type, program_type)",
            "The Option Type must be unique per Program Type !",
        ),
    ]

    @api.model
    def _get_program_values_template(self):
        return {SELF: {}, DISCOUNT_PRODUCT_FNAME: {}}  # sale.coupon.program

    @api.model
    def _get_program_values_cfg(self):
        tmpl_func = self._get_program_values_template
        return {
            "discount_fixed_amount": {
                "label": _("Fixed Amount Discount"),
                "incompatible_options": [],
                "values": {
                    **tmpl_func(),
                    SELF: {"reward_type": "discount", "discount_type": "fixed_amount"},
                },
            },
            "product_sale_ok": {
                "label": _("Product can be Sold"),
                "incompatible_options": ["product_not_sale_ok"],
                "values": {**tmpl_func(), DISCOUNT_PRODUCT_FNAME: {"sale_ok": True}},
            },
            "product_not_sale_ok": {
                "label": _("Product can not be Sold"),
                "incompatible_options": ["product_sale_ok"],
                "values": {**tmpl_func(), DISCOUNT_PRODUCT_FNAME: {"sale_ok": False}},
            },
        }

    def validate_compatibility(self):
        """Validate if multiple options can be used together."""

        def check_incompatible_program_types():
            # Only same program type options can be used together.
            if len(set(self.mapped("program_type"))) != 1:
                raise UserError(err_msg)

        def check_incompatible_option_types():
            incompatible_options = []
            cfg = self._get_program_values_cfg()
            for rec in self:
                opt_type = rec.option_type
                if opt_type in incompatible_options:
                    raise UserError(err_msg)
                incompatible_options.extend(
                    cfg[opt_type].get("incompatible_options", [])
                )

        if len(self) <= 1:
            return True
        err_msg = _("Options '%s' are not compatible") % ", ".join(self.mapped("name"))
        check_incompatible_program_types()
        check_incompatible_option_types()

    def _get_related_record(self, program, path):
        if path == SELF:
            return program
        return operator.attrgetter(path)(program)

    def _prepare_values_from_program(self, program):
        self.ensure_one()
        if self.option_type == "discount_fixed_amount":
            return {"list_price": program.discount_fixed_amount}
        return {}

    def get_program_values(self, program=None):
        """Return program values from related options.

        Values returned are for program and related product.
        """
        # TODO: there is mergedeep external PYPI module that can simplify
        # multiple dictionary merging.
        values = self._get_program_values_template()
        try:
            self.validate_compatibility()
        except UserError:
            return {}  # can't generate values if options incompatible
        cfg = self._get_program_values_cfg()
        for option in self:
            opt_cfg = cfg[option.option_type]
            opt_vals = opt_cfg["values"]
            if program:
                opt_vals[DISCOUNT_PRODUCT_FNAME].update(
                    option._prepare_values_from_program(program)
                )
            opt_keys = opt_vals.keys()
            for key in opt_keys:
                values[key].update(opt_vals[key])
        return values

    def validate_program(self, program, excluded_paths=None):
        """Validate if program values match related option values."""
        if not excluded_paths:
            excluded_paths = []
        for attr_path, values in self.get_program_values().items():
            if attr_path in excluded_paths:
                continue
            record = self._get_related_record(program, attr_path)
            record_data = record.read(fields=list(values.keys()), load=False)[0]
            for fname, val in values.items():
                if record_data[fname] != val:
                    label = record._fields[fname].string
                    raise UserError(
                        _("'%s' value must be '%s' for %s")
                        % (label, val, record._description)
                    )
