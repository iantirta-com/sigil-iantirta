import { Component, onWillRender, useEffect, useExternalListener, useRef } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";


class LoggerField extends Component {
    static template = "karaoke_iantirta.LoggerField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    setup() {
        console.log("Setup", this);
        console.log(this.value);
        useInputField({ getValue: () => this.value });
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    get logs() {
        const rawValue = this.props.record.data[this.props.name];
        if (!rawValue || (typeof rawValue === "string" && rawValue.trim() === "")) {
            return [];
        }
        try {
            return JSON.parse(rawValue);
        } catch (e) {
            console.error("Failed to parse logger data:", e);
            return [];
        }
    }

    formatTime(ts) {
        if (!ts) return "";
        const date = new Date(ts * 1000);
        return date.toLocaleTimeString([], { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    }
    getLevelColor(level) {
        const lvl = (level || 'info').toLowerCase();
        const colors = {
            'info': '#4fc1ff',     // Light Blue
            'asr': '#4ec9b0',      // Mint Green
            'align': '#4ec9b0',    // Mint Green
            'subtitle': '#4fc1ff', // Light Blue
            'error': '#f44747',    // Red
            'warning': '#d7ba7d'   // Yellow
        };
        return colors[lvl] || '#4ec9b0'; // Default fallback
    }
}

const loggerField = {
    component: LoggerField,
    displayName: _t("Logger"),
    supportedTypes: ["char", "text"],
}


registry.category("fields").add("logger", loggerField);
