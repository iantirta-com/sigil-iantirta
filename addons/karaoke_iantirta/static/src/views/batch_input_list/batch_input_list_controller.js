import { ListController } from "@web/views/list/list_controller";

export class BatchInputListController extends ListController {
    static components = {
        ...ListController.components,
    };

    setup() {
        super.setup();
        console.log("OK?")
    }

    onClickBatchInput(ev) {
        this.actionService.doAction(
            "karaoke_iantirta.karaoke_batch_input_wizard_action",
            {
                onClose: async (e) => {
                    await this.model.load();
                    this.model.notify();
                },
            }
        );
    }
};
