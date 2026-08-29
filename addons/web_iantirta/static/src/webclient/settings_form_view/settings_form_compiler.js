import { patch } from "@web/core/utils/patch";
import { SettingsFormCompiler } from "@web/webclient/settings_form_view/settings_form_compiler";
import { append, createElement } from "@web/core/utils/xml";
import { toStringExpression } from "@web/views/utils";

patch(SettingsFormCompiler.prototype, {
    /**
     * @Override
     */
    compileApp(el, params) {
        if (el.getAttribute("notApp") === "1") {
            //An app noted with notApp="1" is not rendered.

            //This hack is used when a technical module defines settings, and we don't want to render
            //the settings until the corresponding app is not installed.

            // For example, when installing the module website_sale, the module sale is also installed,
            // but we don't want to render its settings (notApp="1").
            // On the contrary, when sale_management is installed, the module sale is also installed
            // but in this case we want to see its settings (notApp="0").
            return;
        }
        const module = {
            key: el.getAttribute("name"),
            string: el.getAttribute("string"),
            imgurl:
                el.getAttribute("logo") ||
                "/web_enterprise_iantirta/static/description/" + el.getAttribute("name") + "/icon.png",
        };
        params.modules.push(module);
        const settingsApp = createElement("SettingsApp", {
            key: toStringExpression(module.key),
            string: toStringExpression(module.string || ""),
            imgurl: toStringExpression(module.imgurl),
            selectedTab: "settings.selectedTab",
        });

        for (const child of el.children) {
            append(settingsApp, this.compileNode(child, params));
        }

        params.anchors.push(
            ...[...settingsApp.querySelectorAll("SearchableSetting")]
                .filter((s) => s.id)
                .map((s) => ({ app: module.key, settingId: s.id.replaceAll("`", "") }))
        );
        return settingsApp;
    },

    /**
     * @Override
     */
    compileBlock(el, params) {
        const settingsContainer = createElement("SettingsBlock", {
            title: toStringExpression(el.getAttribute("title") || ""),
            tip: toStringExpression(el.getAttribute("help") || ""),
            icon: toStringExpression(el.getAttribute("icon") || ""),
        });
        for (const child of el.children) {
            append(settingsContainer, this.compileNode(child, params));
        }
        return settingsContainer;
    }
});