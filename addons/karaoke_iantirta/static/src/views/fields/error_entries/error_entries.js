import { Component, onWillRender, useEffect, useExternalListener, useRef, markup } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { stripAnsi } from "../ansi_utils";

class ErrorEntriesField extends Component {
    static template = "karaoke_iantirta.ErrorEntriesField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    stripLogAnsi(text) {
        return stripAnsi(text);
    }

    setup() {
        console.log(this.props.record.data[this.props.name])
    }

    get errors() {
        const raw = this.props.record.data[this.props.name];

        if (!raw) {
            return [];
        }

        let errors_list = null;
        if (typeof raw === 'object' && raw !== null) {
            errors_list = Array.isArray(raw) ? raw : [raw]
        }
        else if (typeof raw === 'string') {
            try {
                const parsed = JSON.parse(raw);
                errors_list = Array.isArray(parsed) ? parsed : [parsed];
            } catch (e) {
                console.error(`Error while handling json error entries: ${e}`);
                return [];
            }
        }

        if (!errors_list) {
            return [];
        }

        return errors_list.map(error => {
            return {
                'name': error[0] || 'Unknown',
                'error_type': error[1] || 'Exception',
                'error_desc': error[2] || 'No description provided.',
                'traceback': error[3] || '', // Assuming index 3 is skipped intentionally
            }
        });
    }
}

const errorEntriesField = {
    component: ErrorEntriesField,
    displayName: _t("ErrorEntries"),
    supportedTypes: ['json'],
}

registry.category("fields").add("error_entries", errorEntriesField);
