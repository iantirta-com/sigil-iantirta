import { Component, onWillRender, useEffect, useExternalListener, useRef, markup } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { stripAnsi } from "../ansi_utils";

class LogEntriesField extends Component {
    static template = "karaoke_iantirta.LogEntriesField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    stripLogAnsi(text) {
        return stripAnsi(text);
    }

    get logs() {
        const raw = this.props.record.data[this.props.name];
        
        if (!raw) {
            return [];
        }

        if (typeof raw === 'object' && raw !== null) {
            return Array.isArray(raw) ? raw : [raw];
        }

        if (typeof raw === 'string') {
            try {
                const parsed = JSON.parse(raw);
                return Array.isArray(parsed) ? parsed : [parsed];
            } catch (e) {
                console.error(`Error while handling json log entries: ${e}`);
                return [];
            }
        }
    }
}

const logEntriesField = {
    component: LogEntriesField,
    displayName: _t("LogEntries"),
    supportedTypes: ['json'],
}

registry.category("fields").add("log_entries", logEntriesField);
