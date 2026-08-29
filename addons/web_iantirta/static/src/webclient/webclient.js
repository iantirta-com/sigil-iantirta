import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { WebSidebar } from "./web_sidebar/web_sidebar";
import { WebClientEnterprise } from "@web_enterprise/webclient/webclient";

patch(WebClientEnterprise, {
    components: {
        ...WebClientEnterprise.components,
        WebSidebar,
    }
});