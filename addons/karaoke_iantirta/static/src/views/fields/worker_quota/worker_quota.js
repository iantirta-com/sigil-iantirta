import { Component, onWillRender, useEffect, useExternalListener, useRef, markup } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { formatDate, formatDateTime } from "@web/views/fields/formatters";
import {
    deserializeDate,
    deserializeDateTime,
    serializeDate,
    serializeDateTime,
    parseDateTime,
    parseDate,
} from "@web/core/l10n/dates";

class WorkerQuotaField extends Component {
    static template = "karaoke_iantirta.WorkerQuotaField";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    setup() {
        this.isColab = this.props.record.data?.code === 'colab';
        console.log("Setup is colab", this.isColab, this.colabQuotaData);
    }

    get quotaAllowed() {
        return this.props.record.data['quota_allowed']
    }
    get quotaUsed() {
        return this.props.record.data['quota_used']
    }
    get quotaRefreshTime() {
        return this.props.record.data['quota_refresh_time']
    }

    get colabQuotaData() {
        if (!this.isColab) return;
        const quota = this.quota || {};
        const data = this.props.record.data;
        console.log(data)
        
        const initial = data.initial_token;
        const remaining = data.remaining_tokens;

        const hasQuota =
            remaining !== null &&
            (
                (initial !== null && initial > 0) ||
                remaining > 0
            );
        const hasBaseline = initial !== null && initial > 0;

        let remainingPercent = null;
        let consumedPercent = null;
        let consumedTokens = null;

        if (hasQuota && hasBaseline) {
            remainingPercent = Math.min(
                100,
                Math.max(0, (remaining / initial) * 100)
            );

            consumedPercent = 100 - remainingPercent;

            consumedTokens = Math.max(0, initial - remaining);
        }

        let colorClass = "bg-success";

        if (remainingPercent !== null) {
            if (remainingPercent <= 10) {
                colorClass = "bg-danger";
            } else if (remainingPercent <= 25) {
                colorClass = "bg-warning";
            }
        }

        const status = !hasQuota
            ? "unknown"
            : remaining > 0
                ? "available"
                : "exhausted";

        const statusLabel = {
            unknown: _t("Quota unknown"),
            available: _t("Quota available"),
            exhausted: _t("Quota exhausted"),
        }[status];

        const statusClass = {
            unknown: "text-bg-secondary",
            available: "text-bg-success",
            exhausted: "text-bg-danger",
        }[status];

        return {
            hasQuota,
            hasBaseline,

            initialTokens: initial,
            remainingTokens: remaining,
            consumedTokens,

            remainingPercent,
            consumedPercent,

            remainingLabel: remaining,
            initialLabel: initial,
            consumedLabel: consumedTokens,

            colorClass,

            status,
            statusLabel,
            statusClass,

            assignmentsCount: quota.assignmentsCount,

            consumptionRate: quota.consumptionRateHourly,

            refillTime: formatDateTime(data.refill_timestamp),

            eligibleGpus: Array.isArray(quota.eligibleGpus)
                ? quota.eligibleGpus
                : [],

            eligibleTpus: Array.isArray(quota.eligibleTpus)
                ? quota.eligibleTpus
                : [],
        };
    }

    /**
     * Helper to parse time strings into total seconds.
     * Handles "HH:MM:SS.mmmmmm" and "X days, HH:MM:SS" formats.
     */
    parseDurationToSeconds(durationStr) {
        if (!durationStr) return 0;
        
        let days = 0;
        let timeStr = durationStr;

        // 1. Extract days if the "X day(s), " prefix exists
        const dayMatch = durationStr.match(/^(\d+)\s+days?,\s+(.*)$/);
        if (dayMatch) {
            days = parseInt(dayMatch[1], 10);
            timeStr = dayMatch[2]; // Leaves just the "HH:MM:SS" part
        }

        // 2. Strip any fractional microseconds (e.g. .304471)
        timeStr = timeStr.split('.')[0]; 

        // 3. Split the hours, minutes, seconds
        const timeParts = timeStr.split(':');
        if (timeParts.length !== 3) return 0;

        const hours = parseInt(timeParts[0], 10);
        const minutes = parseInt(timeParts[1], 10);
        const seconds = parseInt(timeParts[2], 10);

        // 4. Calculate total elapsed seconds
        return (days * 86400) + (hours * 3600) + (minutes * 60) + seconds;
    }

    /**
     * Formats total seconds back into a clean string like "6h 3m" or "1d 6h"
     */
    formatSecondsToLabel(totalSeconds) {
        if (totalSeconds === 0) return "0h";
        
        const d = Math.floor(totalSeconds / 86400);
        const h = Math.floor((totalSeconds % 86400) / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);

        let parts = [];
        if (d > 0) parts.push(`${d}d`);
        if (h > 0) parts.push(`${h}h`);
        if (m > 0 && d === 0) parts.push(`${m}m`); // Only show minutes if less than a day
        
        return parts.join(' ') || "< 1m";
    }

    get quota() {
        const raw = this.props.record.data[this.props.name];
        
        if (!raw) {
            return null;
        }

        if (typeof raw === 'object' && raw !== null) {
            return raw;
        }

        if (typeof raw === 'string') {
            try {
                return JSON.parse(raw);
            } catch (e) {
                console.error(`Error while handling json log entries: ${e}`);
                return null;
            }
        }
    }

    get quotaData() {
        if (!this.quota || !this.quota.types) return null;

        const quotaBars = this.quota.types.map(quotaObj => {
            const typeKey = Object.keys(quotaObj)[0];
            const data = quotaObj[typeKey];
            const usedSec = this.parseDurationToSeconds(data.time_used);
            const allowedSec = this.parseDurationToSeconds(data.time_allowed);
            
            // Calculate percentage safely
            let percent = 0;
            if (allowedSec > 0) {
                percent = Math.min(100, Math.round((usedSec / allowedSec) * 100));
            }

            // Determine bar color based on usage
            let colorClass = "bg-success";
            if (percent > 75) colorClass = "bg-warning";
            if (percent > 90) colorClass = "bg-danger";

            return {
                label: typeKey.toUpperCase(),
                percent: percent,
                colorClass: colorClass,
                usedLabel: this.formatSecondsToLabel(usedSec),
                allowedLabel: this.formatSecondsToLabel(allowedSec),
            };
        });
        let refresh_time = _t("Unknown");
        if (this.quota.refresh_time) {
            refresh_time = formatDateTime(deserializeDateTime(this.quota.refresh_time))
        }
        return {
            bars: quotaBars,
            refreshTime: refresh_time
        }
    }

}

const workerQuotaField = {
    component: WorkerQuotaField,
    displayName: _t("WorkerQuota"),
    supportedTypes: ['json'],
}

registry.category("fields").add("worker_quota", workerQuotaField);
