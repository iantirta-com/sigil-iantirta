import { Component } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { MainComponentsContainer } from "@web/core/main_components_container";

const testRegistry = registry.category("test_components_iantirta")


export class Components extends Component {
    static template = "web_iantirta.components";
    static components = {}
    static props = ["*"]
    
    setup() {
        this.allTest = Object.entries(testRegistry.getAll())
            .map(([name, test]) => ({
                name, ...test
            }))
            .sort((a, b) => a.sequence - b.sequence);
    }
}

export class ComponentsPage extends Component {
    static template = "web_iantirta.ComponentsPage";
    static components = {
        MainComponentsContainer,
        Components,
    }
    static props = ["*"]
}