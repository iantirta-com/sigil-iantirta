import { Component, onWillRender, useEffect, useExternalListener, useRef } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";
const { DateTime } = luxon;


class LoggerField extends Component {
    static template = "karaoke_iantirta.LoggerField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    get logs() {
        try {
            return JSON.parse(this.props.record.data[this.props.name]).map(log => ({
                timestamp: DateTime.fromSeconds(log.timestamp).toFormat("yy-MM-dd HH:mm:ss"),
                level: log.level,
                stage: log.stage,
                message: log.message,
            }));
        } catch {
            return [];
        }
    }
}

const loggerField = {
    component: LoggerField,
    displayName: _t("Logger"),
    supportedTypes: ["char", "text"],
}


registry.category("fields").add("logger", loggerField);
