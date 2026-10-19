import { Component, useState, useEffect, useExternalListener, useRef, markup } from "@sigil/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";


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
    }

    formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async onClickDownload() {
        const uris = this.downloadUris;
        if (!uris.length) return;

        this.state.isDownloading = true;
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

                    if (this.state.totalBytes > 0) {
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
            this.state.isMerging = true;

            // Use a small timeout to let the UI update to "Merging..." before the CPU locks up
            await new Promise(resolve => setTimeout(resolve, 50));

            const mergedVideoBlob = new Blob(downloadedBlobs, { type: 'video/mkv' });
            const localVideoUrl = URL.createObjectURL(mergedVideoBlob);

            const recordName = this.props.record.data.title || 'karaoke_video';
            const fileName = `${recordName}.mkv`;

            const a = document.createElement('a');
            a.href = localVideoUrl;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            a.remove();

            setTimeout(() => URL.revokeObjectURL(localVideoUrl), 10000);

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

const karaokeDownloadUrisField = {
    component: KaraokeDownloadUrisField,
    displayName: _t("KaraokeDownloadUris"),
    supportedTypes: ['json'],
}

registry.category("fields").add("karaoke_download_uris", karaokeDownloadUrisField);
