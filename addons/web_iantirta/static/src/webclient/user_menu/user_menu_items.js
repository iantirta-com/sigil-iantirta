
import { registry } from "@web/core/registry";

const userMenuRegistry = registry.category("user_menuitems");

const supportItem = userMenuRegistry.get("support");
if (supportItem) {
    userMenuRegistry.add("support", (env) => {
        const res = supportItem(env);
        res.icon = "fa-help";
        return res
    }, {force: true});
}