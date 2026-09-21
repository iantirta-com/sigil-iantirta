import { whenReady, Component } from "@sigil/owl";
import { mountComponent } from "@web/env";
import { getTemplate } from "@web/core/templates";
import { ComponentsPage } from "./component";

(async function startComponentsPage() {
    await whenReady();
    const app = await mountComponent(ComponentsPage, document.body, {
        name: "Components Page",
        props: {},
    });
    const { env } = app;
    Component.env = env;
})();
