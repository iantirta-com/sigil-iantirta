import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { KaraokeListController } from "./karaoke_list_controlller";

export const karaokeListView = {
    ...listView,
    Controller: KaraokeListController,
    buttonTemplate: "karaoke.BatchInputListView.Buttons",
};

registry.category("views").add("karaoke_list_view", karaokeListView);
