import { registry } from "@web/core/registry";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Client actions for karaoke reset task with confirmation.
 */
const resetConfirmationMessage = _t(
    `Are you sure you want to reset the task status? Please think twice.`
);

function KaraokeResetTask(env, act_action) {
    const { dialog, action } = env.services;
    const body = resetConfirmationMessage; 
    dialog.add(ConfirmationDialog, {
        body,
        cancel: () => {},
        cancelLabel: _t("No, keep it."),
        confirm: async () => {
            await action.doActionButton({
                type: 'object',
                name: 'action_reset_status',
                resIds: act_action.context.active_ids,
                resModel: act_action.context.active_model,
            });
            await action.doAction('soft_reload');
        },
        confirmLabel: _t("Reset."),
        confirmClass: 'btn-danger',
        title: _t("Reset Tasks"),
    });
}

registry.category("actions").add("karaoke_reset_tasks", KaraokeResetTask);
