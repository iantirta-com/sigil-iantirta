import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu";
import { onMounted, useRef, useState} from "@sigil/owl";
import { fuzzyLookup } from "@web/core/utils/search";

patch(HomeMenu.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
            searchQuery: "",
        });
    },
    get currentUserName() {
        return user.name;
    },

    /**
     * @override
     */
    get displayedApps() {
        const apps = super.displayedApps;
        var query = this.state.searchQuery;
        if (query == "") return apps;
        const result = [];
        fuzzyLookup(query, apps, (menu) => menu.label)
            .forEach((menu) => {
                result.push(menu);
            });
        return result;
    },
});