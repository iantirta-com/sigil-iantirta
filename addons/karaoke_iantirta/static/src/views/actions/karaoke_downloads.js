import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";


// Helper to create and manage a floating progress UI
class DownloadProgressUI {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'position-fixed bottom-0 end-0 p-3';
        this.container.style.zIndex = '9999';
        this.container.innerHTML = `
            <div class="toast show bg-white shadow-lg" role="alert">
                <div class="toast-header bg-primary text-white">
                    <i class="fa fa-download me-2"></i>
                    <strong class="me-auto" id="dl-title">Initializing...</strong>
                    <small id="dl-stats">0/0</small>
                </div>
                <div class="toast-body">
                    <p class="mb-1 text-truncate" id="dl-filename" style="max-width: 250px;">Preparing files...</p>
                    <div class="progress" style="height: 10px;">
                        <div id="dl-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated bg-success" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(this.container);
    }

    update(currentFile, fileIndex, totalFiles, progressPercent) {
        document.getElementById('dl-title').innerText = `Downloading Files`;
        document.getElementById('dl-stats').innerText = `${fileIndex}/${totalFiles}`;
        document.getElementById('dl-filename').innerText = currentFile;
        document.getElementById('dl-progress-bar').style.width = `${progressPercent}%`;
    }

    close() {
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}


async function karaokeDownloads(env, records) {
    console.log("karaoke download", env, records)
    const notification = env.services.notification;
    
    if (!window.showDirectoryPicker) {
        notification.add(
            _t("Auto-streaming requires Chromium-based browsers (Chrome/Edge). Please use a supported browser for mass downloads."),
            { type: "danger" }
        );
        return;
    }
    
    notification.add(_t(`Starting mass download of ${records.length} files. Please do not close this tab.`), { type: "info" });

    try {
        const directoryHandle = await window.showDirectoryPicker({ mode: "readwrite" });
        const ui = new DownloadProgressUI();

        const workerBaseUrl = "https://karaoke-cdn-proxy.iantirta.com";
        let downloaded = 0;
        let skipped = 0;

        for (let r = 0; r < records.length; r++) {
            const record = records[r];

            // const targetResId = record.resId;
            // const suffix = this.fileSuffix;
            const targetTitle = record.data.title || 'karaoke_video';
            
            try {
                let metadata = record.data.download_uris;
                if (typeof metadata === 'string') metadata = JSON.parse(metadata);

                const isLegacy = Array.isArray(metadata);
                const uris = isLegacy ? metadata : (metadata?.files || []);
                const provider = (!isLegacy && metadata?.provider) ? metadata.provider : 'gdrive';

                if (!uris.length) {
                    skipped++;
                    continue;
                }

                const totalChunks = uris.length;
                const fileName = `${targetTitle}.mkv`;

                const fileHandle = await directoryHandle.getFileHandle(fileName, { create: true });
                const writableStream = await fileHandle.createWritable();

                let totalBytesAcrossChunks = 0;
                let bytesWrittenForCurrentFile = 0;

                for (let i = 0; i < totalChunks; i++) {
                    let chunkUri = uris[i];
                    // TODO: Change this into backend server later on
                    // Or instead in the library iantirta.media
                    if (!chunkUri.startsWith('http') && provider == 'hf_dataset') {
                        chunkUri = `https://huggingface.co/datasets/yancovenant/karaoke-archive/resolve/main/${chunkUri}?download=true`
                    }
        
                    const fetchUrl = `${workerBaseUrl}/?source=${encodeURIComponent(chunkUri)}`;
                    const response = await fetch(fetchUrl);
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    
                    // Estimate size for legacy Drive links if we don't have HF metadata size
                    
                    // if (this.state.totalBytes === 0 && contentLength && i === 0) {
                    //     this.state.totalBytes = contentLength * totalChunks;
                    // }

                    const contentLength = parseInt(response.headers.get('content-length') || '0', 10);
                    if (totalBytesAcrossChunks === 0 && contentLength > 0) {
                        totalBytesAcrossChunks = contentLength * totalChunks;
                    }

                    const reader = response.body.getReader();

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        await writableStream.write(value);
                        bytesWrittenForCurrentFile += value.length;

                        if (totalBytesAcrossChunks > 0) {
                            const percent = Math.min(100, Math.round((bytesWrittenForCurrentFile / totalBytesAcrossChunks) * 100));
                            ui.update(`${fileName} (Part ${i + 1}/${totalChunks})`, r + 1, records.length, percent);
                        }
                        // this.state.downloadedBytes += value.length;

                        // if (this.props.record.resId === targetResId && this.state.totalBytes > 0) {
                        //     this.state.progressPercent = Math.min(
                        //         100, 
                        //         Math.round((this.state.downloadedBytes / this.state.totalBytes) * 100)
                        //     );
                        // }
                    }
                }
                await writableStream.close(); // Save file
                downloaded++;

            } catch (error) {
                console.error(`Failed on ${targetTitle}:`, error);
                skipped++;
            }
        }
        ui.close();
        notification.add(
            _t(`Mass download complete! Saved: ${downloaded} | Skipped/Failed: ${skipped}`), 
            { type: "success" }
        );
    } catch (err) {
        console.error("Download manager failed:", err, err.name);
        notification.add(_t("Download sequence interrupted."), { type: "warning" });
    }
}

export function useKaraokeDownloads(env, model) {
    async function getRecords(records = []) {
        let resIds;
        if (!records.length) {
            resIds = await model.root.getResIds(true);
            records = model.root.records.filter((r) => resIds.includes(r.resId));
        }
        return records
    }
    
    return async (records) => {
        records = await getRecords(records);
        karaokeDownloads(env, records);
    };
}

/**
 * Client actions for karaoke mass download.
 */
function KaraokeDownloads(env, action) {
    console.log("Downloading", env, action)
}

registry.category("actions").add("karaoke_downloads", KaraokeDownloads);
