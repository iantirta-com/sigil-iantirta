import { Component, onWillRender, useEffect, useExternalListener, useRef } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";
const { DateTime } = luxon;
import { formatJson } from "@web/views/fields/formatters";


class LogEntriesField extends Component {
    static template = "karaoke_iantirta.LogEntriesField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    get logs() {
        try {
            const raw = this.props.record.data[this.props.name];
            if (raw) {
                return JSON.parse(raw);
            } else {
                return [];
            }
        } catch {
            return [];
        }
    }
}

const logEntriesField = {
    component: LogEntriesField,
    displayName: _t("LogEntries"),
    supportedTypes: ["char", "text", 'json'],
}


registry.category("fields").add("log_entries", logEntriesField);
