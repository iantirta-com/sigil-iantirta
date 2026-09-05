import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { markup } from "@sigil/owl";

patch(ControlPanel.prototype, {
    markupSvgIcon(icon) {
        return markup(icon);
    }
})
