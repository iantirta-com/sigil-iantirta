import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { _t } from "@web/core/l10n/translation";
import { unpatchListRendererDesktop } from "@web_enterprise/views/list/list_renderer_desktop";

unpatchListRendererDesktop();
patch(ListRenderer.prototype, {
    /**
     * @Override
     * Returns the classnames to apply to the row representing the given record.
     * @param {RelationalRecord} record
     */
    getRowClass(record) {
        /**
         * Classnames coming from decorations
         * @type {string[]}
         */
        const classNames = this.props.archInfo.decorations
            .filter((decoration) =>
                evaluateBooleanExpr(decoration.condition, record.evalContextWithVirtualIds)
            )
            .map((decoration) => decoration.class);
        if (record.selected) {
            classNames.push("table-primary");
        }
        // "o_selected_row" classname for the potential row in edition
        if (record.isInEdition) {
            classNames.push("o_selected_row");
        }
        if (record.selected) {
            classNames.push("o_data_row_selected");
        }
        if (this.canResequenceRows) {
            classNames.push("o_row_draggable");
        }
        return classNames.join(" ");
    }
});