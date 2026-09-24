import { Component, onWillRender, useEffect, useExternalListener, useRef } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";


class ErrorTracebackField extends Component {
    static template = "karaoke_iantirta.ErrorTracebackField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    get error() {
        return JSON.parse(this.props.record.data[this.props.name]);
    }
}

const errorTracebackField = {
    component: ErrorTracebackField,
    displayName: _t("Error Traceback"),
    supportedTypes: ["char", "text"],
}


registry.category("fields").add("error_traceback", errorTracebackField);
