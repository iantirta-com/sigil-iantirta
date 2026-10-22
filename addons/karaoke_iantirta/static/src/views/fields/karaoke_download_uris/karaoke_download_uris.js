import { Component, useState, useEffect, useExternalListener, useRef, markup } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { humanSize } from "@web/core/utils/binary";


class KaraokeDownloadUrisField extends Component {
    static template = "karaoke_iantirta.KaraokeDownloadUris";
    static components = {}
    static props = {
        ...standardFieldProps,
    }

    setup() {
        this.state = useState({
            isDownloading: false,
            downloadedBytes: 0,
            totalBytes: 0,
            progressPercent: 0,
        });
        this.notification = useService("notification");

        this.isLegacy = false;
    }

    formatBytes(bytes) {
        return humanSize(bytes);
    }

    _legacyDownload(uris) {
        // Support gdrive
        if (!uris.length) return;
    }

    _download(metadata) {
        // support hf
        // this metadata consist of:
        // - suffix, count, size, files
        if (!metadata.files.length) return;
        
    }

    async onClickDownload() {
        const uris = this.downloadUris;
        if (this.isLegacy) {
            return _legacyDownload(uris);
        }
        else {
            return _download(uris)
        }
        if (!uris.length) return;

        const targetTitle = this.props.record.data.title || 'karaoke_video';
        const targetResId = this.props.record.resId;

        this.state.isDownloading = true;
        this.state.activeResId = targetResId;
        this.state.isMerging = false;
        this.state.downloadedBytes = 0;
        this.state.totalBytes = 0;
        this.state.progressPercent = 0;
        this.state.errorMessage = "";

        const totalChunks = uris.length;
        const downloadedBlobs = [];
        const workerBaseUrl = "https://karaoke-cdn-proxy.iantirta.com";

        try {
            for (let i = 0; i < totalChunks; i++) {
                const chunkUri = uris[i];
                const fetchUrl = `${workerBaseUrl}/?source=${encodeURIComponent(chunkUri)}`;
                
                const response = await fetch(fetchUrl);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                
                const contentLength = parseInt(response.headers.get('content-length') || '0', 10);
                if (contentLength && i === 0) {
                    // Estimate total file size assuming equal chunk sizes
                    this.state.totalBytes = contentLength * totalChunks;
                }
                
                const reader = response.body.getReader();
                const chunkUint8Arrays = [];

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    chunkUint8Arrays.push(value);
                    this.state.downloadedBytes += value.length;

                    if (this.props.record.resId === targetResId && this.state.totalBytes > 0) {
                        this.state.progressPercent = Math.min(
                            100, 
                            Math.round((this.state.downloadedBytes / this.state.totalBytes) * 100)
                        );
                    }
                }

                const chunkBlob = new Blob(chunkUint8Arrays);
                downloadedBlobs.push(chunkBlob);
            }

            // Enter merging phase
            if (this.props.record.resId === targetResId) {
                this.state.isMerging = true;
            }

            // Use a small timeout to let the UI update to "Merging..." before the CPU locks up
            await new Promise(resolve => setTimeout(resolve, 50));

            const mergedVideoBlob = new Blob(downloadedBlobs, { type: 'video/mkv' });
            const localVideoUrl = URL.createObjectURL(mergedVideoBlob);

            const fileName = `${targetTitle}.mkv`;

            const a = document.createElement('a');
            a.href = localVideoUrl;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            a.remove();

            setTimeout(() => URL.revokeObjectURL(localVideoUrl), 10000);
            
            this.notification.add(_t(`Successfully downloaded ${fileName}`), { type: "success" });
        } catch (error) {
            console.error("Download failed:", error);
            this.state.errorMessage = error.message || "Network error occurred";
        } finally {
            // Reset UI back to default state
            this.state.isDownloading = false;
            this.state.isMerging = false;
        }
    }

    get downloadUris() {
        const raw = this.props.record.data[this.props.name];
        
        if (!raw) {
            return [];
        }

        if (typeof raw === 'object' && raw !== null) {
            if (Array.isArray(raw)) {
                this.isLegacy = true;
                return raw
            } else {
                this.isLegacy = false;
                return raw
            }
        }

        if (typeof raw === 'string') {
            try {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed)) {
                    this.isLegacy = true;
                    return parsed;
                } else {
                    this.isLegacy = false;
                    return parsed;
                }
            } catch (e) {
                console.error(`Error while handling json log entries: ${e}`);
                return [];
            }
        }
    }
}

const karaokeDownloadUrisField = {
    component: KaraokeDownloadUrisField,
    displayName: _t("KaraokeDownloadUris"),
    supportedTypes: ['json'],
}

registry.category("fields").add("karaoke_download_uris", karaokeDownloadUrisField);
