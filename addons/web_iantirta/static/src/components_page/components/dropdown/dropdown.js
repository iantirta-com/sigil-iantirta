import { registry } from "@web/core/registry";
import { Component, xml } from "@sigil/owl";
import { BaseTest } from "../base_component";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";


class SimpleDropdown extends Component {
    static components = { Dropdown, DropdownItem };
    static props = ["*"];
    static template = xml`
        <Dropdown t-props="props">
            <button>Dropdown</button>
            <t t-set-slot="content">

            </t>
        </Dropdown>
    `;
}

class MultiLevelDropdown extends Component {
    static components = { Dropdown, DropdownItem };
    static props = [];
    static template = xml`
        <Dropdown t-props="props">
            <button class="dropdown-a">A</button>
            <t t-set-slot="content">
                <DropdownItem class="'item-a'">Item A</DropdownItem>
                <Dropdown t-props="props">
                    <button class="dropdown-b">B</button>
                    <t t-set-slot="content">
                        <DropdownItem class="'item-b'">Item B</DropdownItem>
                        <Dropdown t-props="props">
                            <button class="dropdown-c">C</button>
                            <t t-set-slot="content">
                                <DropdownItem class="'item-c'">Item C</DropdownItem>
                            </t>
                        </Dropdown>
                    </t>
                </Dropdown>
            </t>
        </Dropdown>
    `;
}

export class DropdownDebugComponent extends BaseTest {
    setup() {
        this.defaultComponent = Dropdown;
        super.setup();
        this.title = "Dropdown";
    }

    setupTest() {
        this.addTest("Default", {}, SimpleDropdown);
        this.addTest("Multi Level", {}, MultiLevelDropdown);
        this.addTest("No Bottom Sheet", {
            bottomSheet: false,
        }, SimpleDropdown)
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
    
    get defaultComponentProps() {
        return {
            items: this.items,
        }
    };
}

registry.category("test_components_iantirta").add("dropdown", {
    sequence: 5,
    component: DropdownDebugComponent,
});
