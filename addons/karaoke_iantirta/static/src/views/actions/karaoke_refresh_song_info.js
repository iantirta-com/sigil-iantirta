import { registry } from "@web/core/registry";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Client actions for karaoke refresh song info task with confirmation.
 */
const refreshConfirmationMessage = _t(
    `Are you sure you want to refresh song information?`
);

function KaraokeRefreshSongInfo(env, act_action) {
    const { dialog, action } = env.services;
    const body = refreshConfirmationMessage; 
    dialog.add(ConfirmationDialog, {
        body,
        cancel: () => {},
        cancelLabel: _t("Cancel."),
        confirm: async () => {
            await action.doActionButton({
                type: 'object',
                name: 'action_refetch_info',
                resIds: act_action.context.active_ids,
                resModel: act_action.context.active_model,
            });
            await action.doAction('soft_reload');
        },
        confirmLabel: _t("Confirm."),
        title: _t("Refresh Songs info"),
    });
}

registry.category("actions").add("karaoke_refresh_song_info", KaraokeRefreshSongInfo);
