import { ListController } from "@web/views/list/list_controller";
import { _t } from "@web/core/l10n/translation";
import { useKaraokeDownloads } from "../actions/karaoke_downloads";

export class KaraokeListController extends ListController {
    static components = {
        ...ListController.components,
    };

    setup() {
        super.setup();
        this.isKaraokeDownloadsEnable = true;
        console.log(this);
        this.KaraokeDownloads = useKaraokeDownloads(this.env, this.model);
    }

    /**
     * Batch Input
     */
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

    /**
     * Batch Download
     */
    getStaticActionMenuItems() {
        return {
            ...super.getStaticActionMenuItems(),
            downloads: {
                isAvailable: () => this.isKaraokeDownloadsEnable,
                sequence: 0,
                icon: 'fa fa-download',
                description: _t("Downloads"),
                callback: () => this.KaraokeDownloads(),
            }
        }
    }
};
