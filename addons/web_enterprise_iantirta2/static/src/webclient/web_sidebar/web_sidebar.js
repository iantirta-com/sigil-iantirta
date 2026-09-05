import {
    Component,
    useExternalListener,
    onMounted,
    onPatched,
    onWillUpdateProps,
    useState,
    useRef,
    useEffect,
    reactive,
} from "@sigil/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { computeAppsAndMenuItems, reorderApps } from "@web/webclient/menus/menu_helpers";
import { registry } from "@web/core/registry";


const systrayRegistry = registry.category("systray");


export class WebSidebar extends Component {
    static template = "web_enterprise_iantirta.WebSidebar";
    
    setup () {
        this.menus = useService("menu");
        this.command = useService("command");
        this.ui = useService("ui");
        
        this.root = useRef("root");

        this.state = useState({
            isCollapsed: false,
            isMobileOpen: false,
        });

        let adaptCounter = 0;
        const renderAndAdapt = () => {
            adaptCounter++;
            this.render();
        };
        systrayRegistry.addEventListener("UPDATE", renderAndAdapt);
        this.env.bus.addEventListener("MENUS:APP-CHANGED", renderAndAdapt);

        // We don't want to adapt every time we are patched
        // rather, we adapt only when menus or systrays have changed.
        useEffect(
            () => {
                this.adapt();
            },
            () => [adaptCounter]
        );

        document.body.classList.add("o_home_menu_background");
        this.env.bus.addEventListener("HOME-MENU:TOGGLED", () => {
            document.body.classList.add("o_home_menu_background");
        });
    }

    get currentApp() {
        return this.menus.getCurrentApp();
    }

    /**
     * Adapt will check the available width for the app sections to get displayed.
     * If not enough space is available, it will replace by a "more" menu
     * the least amount of app sections needed trying to fit the width.
     *
     * NB: To compute the widths of the actual app sections, a render needs to be done upfront.
     *     By the end of this method another render may occur depending on the adaptation result.
     */
    async adapt() {
        return this.render();
    }

    /**
     * @returns {Object[]}
     */
    get displayedApps() {
        const apps = reactive(
            computeAppsAndMenuItems(this.menus.getMenuAsTree("root")).apps
        );
        return apps;
    }

    /**
     * @private
     * @param {Object} menu
     * @returns {Promise}
     */
    _openMenu(menu) {
        return this.menus.selectMenu(menu);
    }

    /**
     * @private
     * @param {Object} app
     */
    _onAppClick(app) {
        this._openMenu(app);

        // auto close on mobile?!
        if (this.ui.isSmall) {
            this.state.isMobileOpen = false;
        }
    }

    /**
     * 
     */
    onClickSearchInput() {
        this.command.openMainPalette();
    }

    /**
     * 
     */
    toggleSidebarCollapse() {
        // this.root.el.classList.toggle("ie_web_sidebar_collapsed");
        this.state.isCollapsed = !this.state.isCollapsed;
    }

    /**
     * 
     */
    toggleMobileSidebar() {
        this.state.isMobileOpen = !this.state.isMobileOpen;
    }
}
