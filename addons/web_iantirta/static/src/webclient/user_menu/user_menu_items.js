import { Component, markup } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { isMacOS } from "@web/core/browser/feature_detection";
import { user } from "@web/core/user";
import { imageUrl } from "@web/core/utils/urls";

const userMenuRegistry = registry.category("user_menuitems");


class ProfileSummary extends Component {
    static template = "web.profileSummary";
    setup() {
        const { partnerId, writeDate, name } = user;
        this.userName = name;
        this.source = imageUrl("res.partner", partnerId, "avatar_128", { unique: writeDate });
    }
}

userMenuRegistry.add("profile_summary", (env) => {
    return {
        type: "component",
        id: "summary",
        sequence: 1,
        contentComponent: ProfileSummary,
    };
});
userMenuRegistry.add("profile_separator", (env) => {
    return {
        type: "separator",
        sequence: 2,
    };
})

const supportItem = userMenuRegistry.get("support");
if (supportItem) {
    userMenuRegistry.add("support", (env) => {
        const res = supportItem(env);
        res.icon = "fa-question-circle";
        return res;
    }, {force: true});
}
const shortcutItem = userMenuRegistry.get("shortcuts");
if (shortcutItem) {
    userMenuRegistry.add("shortcuts", (env) => {
        const res = shortcutItem(env);
        res.icon = "fa-keyboard-o";
        res.description = markup`
            <div class="d-flex align-items-center justify-content-between p-0 w-100">
                <span>${_t("Shortcuts")}</span>
                <span class="o_sigil_kbd_shortcut fw-bold">${isMacOS() ? "CMD" : "CTRL"}+K</span>
            </div>`;
        return res;
    }, {force:true});
}

const prefItem = userMenuRegistry.get("preferences");
if (prefItem) {
    userMenuRegistry.add("preferences", (env) => {
        const res = prefItem(env);
        res.icon = "fa-sliders";
        return res;
    }, {force:true});
}

const accountItem = userMenuRegistry.get("sigil_account");
if (accountItem) {
    userMenuRegistry.add("sigil_account", (env) => {
        const res = accountItem(env);
        res.icon = "fa-user-circle-o";
        res.hide = !env.debug;
        return res;
    }, {force:true});
}

const pwaItem = userMenuRegistry.get("install_pwa");
if (pwaItem) {
    userMenuRegistry.add("install_pwa", (env) => {
        const res = pwaItem(env);
        res.icon = "fa-download";
        return res;
    }, {force:true});
}

const logoutItem = userMenuRegistry.get("log_out");
let logout_sequence = 70;
if (logoutItem) {
    userMenuRegistry.add("log_out", (env) => {
        const res = logoutItem(env);
        res.description = markup`
            <div class="text-danger d-flex align-items-center gap-2 p-0 w-100">
                <i class="fa fa-fw fa-sign-out"></i>
                ${_t(res.description)}
            </div>`;
        logout_sequence = res.sequence;
        return res;
    }, {force:true});
}
userMenuRegistry.add("log_out_separator", (env) => {
    return {
        type: "separator",
        sequence: logout_sequence - 5,
    };
})