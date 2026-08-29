import { patch } from "@web/core/utils/patch";
import { SettingsBlock } from "@web/webclient/settings_form_view/settings/settings_block";

patch(SettingsBlock, {
    props: {
        ...SettingsBlock.props,
        icon: { type: String, optional: true },
    }
});

// SettingsBlock.props = [...SettingsBlock.props, icon: { type: String, optional: true },]