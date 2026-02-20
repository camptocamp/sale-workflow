import {WebsiteSale} from "@website_sale/interactions/website_sale";
import {patch} from "@web/core/utils/patch";

patch(WebsiteSale.prototype, {
    /**
     * Catch the rounding method
     *
     * @override
     */
    async start() {
        const res = await super.start(...arguments);
        // Capture the rounding method on quantity change, either by +/- buttons
        this.el.addEventListener(
            "pointerdown",
            (ev) => {
                const minus = ev.target.closest(".css_quantity_minus");
                const plus = ev.target.closest(".css_quantity_plus");
                if (!minus && !plus) return;
                const parent = (minus || plus).closest(".js_product");
                if (!parent) return;
                parent.dataset.multipleRounding = minus ? "DOWN" : "UP";
            },
            true
        );
        // Capture the rounding method when the user directly inputs a quantity
        this.el.addEventListener(
            "input",
            (ev) => {
                const input = ev.target.closest('input[name="add_qty"]');
                if (!input) return;
                const parent = input.closest(".js_product");
                if (!parent) return;
                if (ev.inputType) {
                    parent.dataset.multipleRounding = "UP";
                }
            },
            true
        );

        return res;
    },
    /**
     * Update the combination info params with the multiple rounding method
     *
     * @override
     */
    _getOptionalCombinationInfoParam(parent) {
        const params = super._getOptionalCombinationInfoParam?.(parent) || {};
        const rounding = parent?.dataset?.multipleRounding;
        if (rounding) {
            params.multiple_rounding = rounding;
        }
        return params;
    },
    /**
     * Force the displayed quantity to the rounded one
     * when multiple is enabled (sale_multiple_uom_id is set).
     *
     * This makes the user see the rounded qty immediately after +/- or variant changes,
     * because those actions trigger a combination refresh.
     *
     * @override
     */
    _onChangeCombination(ev, parent, combination) {
        const result = super._onChangeCombination(...arguments);
        const qtyInput = parent?.querySelector?.('input[name="add_qty"]');
        if (!qtyInput) {
            return;
        }
        if (combination?.is_multiple && combination?.multiple_qty !== null) {
            const rounded = Number(combination.multiple_qty);
            if (!Number.isNaN(rounded)) {
                if (Number(qtyInput.value || 0) !== rounded) {
                    qtyInput.value = rounded;
                }
            }
        }
        return result;
    },
});
