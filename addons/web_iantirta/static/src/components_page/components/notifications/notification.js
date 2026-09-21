import { registry } from "@web/core/registry";
import { onPatched, xml } from "@sigil/owl";
import { BaseTest } from "../base_component";
import { Notification } from "@web/core/notifications/notification";


export class NotificationDebugComponent extends BaseTest {
    setup() {
        this.defaultComponent = Notification;
        super.setup();
        this.title = "Notification";
        onPatched(() => {
            this.target.el.classList.add("o_notification_manager", "position-relative", "top-0", "bottom-0", "start-0", "end-0");
        })
    }

    setupTest() {
        this.addTest("Default");
        this.addTest("Action", {
            title: "With Action",
            buttons: [
                {
                    name: "Action 1",
                    onclick: () => this.noop,
                }
            ]
        });
        this.addTest("Multi Line", {
            message: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed et diam blandit, hendrerit nisl vel, semper nunc. Suspendisse vitae augue blandit, ultricies arcu ut, tempor eros. Donec dapibus ante id ipsum scelerisque, vehicula mollis nunc cursus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Fusce erat enim, euismod in nisi id, varius aliquet quam. Morbi sagittis odio a malesuada eleifend. In hac habitasse platea dictumst. Nulla sed risus eget lacus consectetur elementum."
        });
        this.addTest("Multi Actions", {
            buttons: [
                {
                    name: "Action 1",
                    onclick: () => this.noop,
                },
                {
                    name: "Action 2",
                    onclick: () => this.noop,
                },
                {
                    name: "Action 3",
                    onclick: () => this.noop,
                }
            ]
        });
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
            message: "This is a test notification",
            type: "danger",
            close: this.noop,
        }
    };
}

registry.category("test_components_iantirta").add("notification", {
    sequence: 20,
    component: NotificationDebugComponent,
});