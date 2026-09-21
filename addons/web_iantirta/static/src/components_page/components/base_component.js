import { Component, xml, useRef, useEffect, useState } from "@sigil/owl";
import { deepMerge } from "@web/core/utils/objects";


export class BaseDebugComponent extends Component {
    static template = xml`
        <div class="py-3" t-ref="base_main">
            <div t-out="props.title"/>
            <t t-slot="default"/>
            <t t-slot="actions"/>
        </div>
    `;
    static props = {
        title: { type: String },
    }
}

export class BaseTest extends Component {
    static template = xml`
        <BaseDebugComponent title="title">
            <div t-ref="main">
                <t t-if="state.isReady">
                    <div class="component-item" t-foreach="tests" t-as="test" t-key="test.name">
                        <div t-out="test.name"/>
                        <t t-component="test.component" t-props="getProps(test)"/>
                    </div>
                </t>
            </div>
        </BaseDebugComponent>
    `;
    static components = { BaseDebugComponent };
    static props = {
        title: { type: String },
    };
    static defaultProps = {
        title: "Any Component"
    };

    setup() {
        this.state = useState({
            isReady: false,
        })
        this.tests = [];
        this.title = this.props.title;
        this.target = useRef("main");
        this.setupTest();
        useEffect(
            (el) => {
                console.log(this.tests);
                this.state.isReady = true;
            },
            () => [this.target.el]
        );
    }

    setupTest() {
        return
    }
    
    addTest(name, props = {}, component = this.defaultComponent) {
        if (!component) {
            throw new Error(`Component is required for test "${name}"`);
        }
        this.tests.push({
            name,
            component,
            props,
        });
    }

    getProps(test) {
        return deepMerge(this.defaultComponentProps, test.props);
    }

    get noop() {
        return () => {};
    }

    get defaultComponentProps() {
        return {}
    }
}