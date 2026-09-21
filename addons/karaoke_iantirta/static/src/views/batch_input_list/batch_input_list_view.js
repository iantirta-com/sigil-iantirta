import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { BatchInputListController } from "./batch_input_list_controller";

export const batchInputListView = {
    ...listView,
    Controller: BatchInputListController,
    buttonTemplate: "karaoke.BatchInputListView.Buttons",
};

registry.category("views").add("batch_input_list", batchInputListView);
