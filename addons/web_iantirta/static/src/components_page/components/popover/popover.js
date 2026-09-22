import { registry } from "@web/core/registry";
import { onPatched, reactive } from "@sigil/owl";
import { BaseTest } from "../base_component";
import { Popover } from "@web/core/popover/popover";
import { DropdownPopover } from "@web/core/dropdown/_behaviours/dropdown_popover";


export class PopoverDebugComponent extends BaseTest {
    setup() {
        this.defaultComponent = Popover;
        super.setup();
        this.title = "Popover";
        onPatched(() => {
            let maxBottomEdge = 0;
            Array.from(this.target.el.children).forEach(child => {
                const childBottomEdge = child.offsetTop + child.offsetHeight;
                if (childBottomEdge > maxBottomEdge) {
                    maxBottomEdge = childBottomEdge;
                }
            });
            this.target.el.style.minHeight = `${maxBottomEdge}px`

        });
    }

    setupTest() {
        this.addTest("Default");
        // TODO: Make parent height the same without
        // adding position relative
        this.addTest("Dropdown Class", {
             // Popover Class
            class: "o-dropdown--menu dropdown-menu mx-0 z-1",
        });
        // const state = useDropdownState();
        // const nesting = useDropdownNesting(state);
        // state.open();
        // console.log(nesting);
        // const state2 = useDropdownState()
        // const nesting2 = useDropdownNesting(state2);
        // console.log(nesting2);
        // // TODO: Mock Nesting
        // this.addTest("Nesting", {
        //     // Popover Class
        //     class: "o-dropdown--menu dropdown-menu mx-0 o-dropdown--menu-submenu",
        //     componentProps: {
        //         slots: {
        //             content: xml`hhhhHello`,
        //         }
        //     }
        // });
    }

    get items() {
        return [
            {
                label: "Item 1",
                onSelected: this.noop,
                class: ""
            },
            {
                label: "Item 2",
                onSelected: this.noop,
                class: ""
            }
        ];
    };
    
    get nestedItems() {
        return [
            ...this.items,
        ]
    };
    
    get defaultComponentProps() {
        return {
            component: DropdownPopover,
            componentProps: {
                refresher: reactive({ token: 0 }),
                items: this.items,
            },
            target: this.target,
            close: this.noop,
            role: "menu",
        }
    };
}

registry.category("test_components_iantirta").add("popover", {
    sequence: 10,
    component: PopoverDebugComponent,
});
