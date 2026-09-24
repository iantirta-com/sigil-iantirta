#@title Karaoke Plus
from __future__ import annotations

import time
import traceback
import argparse
import concurrent.futures
import logging
import subprocess
import typing as t
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path

import kplus
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from kplus import config, env
from kplus.pipelines import (
    align2ref,
    detect_audio_activity,
    ensure_file,
)
from kplus.pipelines.asr.hf import HFModel
from kplus.pipelines.separate import BaseSeparator, DemucsSeparator
from kplus.pipelines.utils import ASRResult
from kplus.tools.render import Render

# Logging Setup
opt = argparse.Namespace(log_level="debug")
config.parse_config(opt, setup_logging=True)
logger = logging.getLogger(__name__)


if t.TYPE_CHECKING:
    from kplus.pipelines import DownloadResult
    from kplus.pipelines.asr.hf.mixin import ASRMixin
    from kplus.pipelines.utils import ASRResult, AudioSegment


# Types
TaskStatus: t.TypeAlias = t.Literal[
    "waiting",
    "processing",
    "completed",
    "error",
]
TaskType: t.TypeAlias = t.Literal["basic", "plus"]
LogLevel: t.TypeAlias = t.Literal[
    "debug",
    "info",
    "warning",
    "error",
]
PipelineStage: t.TypeAlias = t.Literal[
    "queued",
    "downloading",
    "separating",
    "detecting",
    "transcribing",
    "aligning",
    "rendering",
    "uploading",
    "completed",
    "error",
]


@dataclass(slots=True)
class Task:
    """ Hold Task Type """
    id: int
    title: str
    artist: str
    duration: float
    lyrics: str
    status: TaskStatus
    url: str
    karaoke_type: TaskType

    # Processing helper
    videopath: str | None = None
    audiopath: str | None = None
    instpath: str | None = None
    samplerate: int | None = None
    audiosegments: AudioSegment | None = None
    result: ASRResult | None = None

    error: dict | None = None
    
    # Complete
    karaokepath: str | None = None
    download_url: str | None = None
    drive_folder_id: str | None = None
    drive_file_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(
            id=int(data["id"]),
            title=data["title"],
            artist=data["artist"],
            duration=float(data["duration"]),
            lyrics=data["lyrics"],
            status=t.cast(TaskStatus, data["status"]),
            url=data["url"],
            karaoke_type=t.cast(TaskType, data["karaoke_type"]),
        )

    def to_dict(self) -> dict:
        """ will return the value needed and
            will be passed to backend
        """
        return {
            "id": self.id,
            "error": self.error,
            "download_url": self.download_url,
            "drive_folder_id": self.drive_folder_id,
            "drive_file_id": self.drive_file_id,
        }

@dataclass(slots=True, frozen=True)
class LogEvent:
    """ Hold Log Event. """
    timestamp: float = field(default_factory=time.time,)
    message: str = ""
    level: LogLevel = "info"

    # Task Specific
    task_id: int | None = None
    stage: PipelineStage = "queued"

class Log:
    """ Custom Log for backend server. """
    def __init__(
        self,
        api: IantirtaAPI,
        *,
        flush_size: int = 20,
        flush_interval: float = 5.0,
    ):
        """"""
        self.api = api

        self.flush_size = flush_size
        self.flush_interval = flush_interval
        
        self._events: list[LogEvent] = []
        self._last_flush = time.monotonic()


    def flush(self) -> None:
        """ Send buffered events to the backend.

            If reporting fails, keep the events so the final flush
            can retry them.
        """
        if not self._events:
            return
        events = self._events
        try:
            self.api.post_events(events)
        except Exception:
            logging.exception(
                "Failed to send worker events to backend."
            )
            return

        self._events.clear()
        self._last_flush = time.monotonic()

    
    def flush_if_needed(self) -> None:
        """ Flush based on event count or
            elapsed time.
        """
        if not self._events:
            return

        elapsed = time.monotonic() - self._last_flush
        is_overflow = len(self._events) >= self.flush_size
        is_passed_time = elapsed >= self.flush_interval
        if is_overflow or is_passed_time:
            self.flush()
        
    def __call__(
        self,
        *,
        task: Task | None,
        stage: PipelineStage,
        message: str,
        level: LogLevel = "info",
    ):
        """"""

        # Log
        log_method = getattr(
            logging.getLogger(__name__),
            level,
        )
        prefix = (
            f"[Task {task.id}] "
            if task
            else "[Worker] "
        )
        log_method("%s%s: %s", prefix, stage, message,)

        # Backend
        self._events.append(LogEvent(
            task_id=task.id if task else None,
            stage=stage,
            message=message,
            level=level,
        ))
        self.flush_if_needed()


class DriveStorage:
    """ Drive Storage API
    """
    def __init__(
        self,
        user_token: dict,
        root_folder_id: str,
    ):
        self.user_token: dict = user_token
        self.root_folder_id: str = root_folder_id
        self.creds: Credentials = Credentials.from_authorized_user_info(
            self.user_token
        )

    def _get_or_create_folder(
        self,
        service,
        folder_name: str,
        parent_id: str | None = None,
    ) -> str:
        """ Will return folder_id needed to put the file
        """
        query = (
            f"name='{folder_name}' "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"

        response = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        if files := response.get('files', []):
            return files[0]['id']

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()

        return folder.get('id')


    def upload(self, task: Task) -> Task:
        """ Upload necessary file to the storage
        """
        service = build(
            'drive', 'v3',
            credentials=self.creds
        )

        karaoke_path = Path(task.karaokepath)
        task.drive_folder_id = self._get_or_create_folder(
            service, task.artist, self.root_folder_id
        )

        request = service.files().create(
            body={
                'name': karaoke_path.name,
                'parents': [task.drive_folder_id]
            },
            media_body=MediaFileUpload(
                str(karaoke_path),
                mimetype='video/x-matroska', # MKV
                resumable=True
            ),
            fields='id, webViewLink, webContentLink',
            supportsAllDrives=True,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.debug(f"Upload progress for Task {task.id}: {int(status.progress() * 100)}%")
        
        task.drive_file_id = response.get('id')
        task.download_url = response.get('webContentLink')

        service.permissions().create(
            fileId=task.drive_file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            },
            fields='id'
        ).execute()

        logger.info(
            f"Successfully uploaded Task {task.id} to Drive. File ID: {task.drive_file_id}"
        )
        karaoke_path.unlink(missing_ok=True)

        return task



class APIError(Exception):
    """ Handle API Error """

class IantirtaAPI:
    """ Manage communication to server API.
    """
    def __init__(
        self,
        api_url: str,
        api_token: str,
        worker_id: int,
        *,
        timeout: float = 30.0
    ):
        """
        """
        self.api_url = api_url
        self.api_token = api_token
        self.worker_id = worker_id
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
        })

    def _post(self, path: str, params: dict):
        """ POST to iantirta.com.
            and add authentication layer here.
        """
        url = f"{self.api_url}{path}"
        payload = {
            "worker_id": self.worker_id,
            "access_token": self.api_token,
        }
        payload.update(params)
        
        response = self.session.post(
            url,
            json={"params": payload},
            timeout=self.timeout,
            allow_redirects=False,
        )
        # Keep redirect handling explicit because
        # the existing API nginx
        # currently redirecting http to https.
        if response.is_redirect:
            redirect_url = response.headers["Location"]
            response = self.session.post(
                redirect_url,
                json={"params": payload},
                timeout=self.timeout,
            )
        
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            raise APIError(f"iantirta API error: {data}")

        return data["result"]


    # Worker
    def worker_start(self, tasks: list[Task]) -> None:
        """ Worker Start
            When worker starting, we will also change
            the task status to processing in backend.
        """
        self._post(
            "/karaoke/worker",
            {
                "action": "start",
                "task_ids": [task.id for task in tasks]
            }
        )

    def worker_stop(self):
        """ Worker Stop
        """
        self._post(
            "/karaoke/worker",
            {
                "action": "stop",
            }
        )

    # Tasks
    def claim_tasks(self, limit=None) -> list[Task]:
        """
        """
        result = self._post(
            "/karaoke/tasks",
            {
                "action": "get",
                "domain": [("status", "=", "waiting")],
                "limit": limit,
            }
        )
        return [
            Task.from_dict(item)
            for item in result
        ]

    def finish_tasks(self, tasks: list[Task]) -> None:
        """
        """
        self._post(
            "/karaoke/tasks",
            {
                "action": "update",
                "tasks": [task.to_dict() for task in tasks]
            }
        )

    # Event
    def post_events(self, events: list[LogEvent]) -> None:
        """
        """
        if not events:
            return

        self._post(
            "/karaoke/tasks",
            {
                "action": "events",
                "events": [asdict(event) for event in events]
            }
        )
        


class Pipeline:
    """ Executes Karaoke Pipeline Procesing.
    """
    def __init__(
        self,
        *,
        cookiefile: str,
        log: Log,
        download_workers: int = 5,
        render_workers: int = 3,
        storage: DriveStorage = None,
    ):
        self.cookiefile = cookiefile
        self.log = log
        self.download_workers = download_workers
        self.render_workers = render_workers
        self.storage = storage
    
    def download(self, task: Task) -> Task:
        """ Download task source url, and populate it.
        """
        self.log(
            task=task,
            stage="downloading",
            message="Downloading Source."
        )
        result: DownloadResult = ensure_file(
            inputpath=task.url,
            external_id=task.id,
            no_lyrics=task.karaoke_type == "basic",
            cookiefile=self.cookiefile,
        )
        # TODO: Manage between server side
        #       title, artist, duration, lyrics.
        task.videopath = result.filepath
        if not task.lyrics and result.lyrics:
            task.lyrics = result.lyrics
        
        return task
                    

    def separate(self, task: Task, separator) -> Task:
        """ Separate task audio, separator class must be pass.
        """
        # Normalize to wav
        self.log(
            task=task,
            stage="separating",
            message="Separating Vocals and Instrumental."
        )
        inputpath = Path(task.videopath).expanduser().resolve()
        mixpath = inputpath.with_suffix(".wav")
        subprocess.run([
            "ffmpeg", "-y", "-i",
            str(inputpath), "-vn",
            "-ar", str(separator.sr),
            "-ac", str(separator.ac),
            str(mixpath)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Run separation
        result: SeparationResult = separator.separate(mixpath)
        
        task.instpath = result.inst_path
        if task.karaoke_type == "plus":
            task.audiopath = result.vocs_path
            task.samplerate = result.sr

        mixpath.unlink(missing_ok=True)

        return task
        

    def detect_audio_activity(self, task: Task) -> Task:
        """"""
        self.log(
            task=task,
            stage="detecting",
            message="Detecting Audio Activity."
        )
        result = detect_audio_activity(
            audio=task.audiopath,
            sr=task.samplerate,
            no_show=True,
            resample=False,
            use_html=False,
        )
        task.audiosegments = result.segments
        return task
            

    def transcribe(self, task: Task, transcriber) -> Task:
        """"""
        self.log(
            task=task,
            stage="transcribing",
            message="Transcribing."
        )
        result = transcriber.transcribe(
            audio=task.audiopath,
            audiosegments=task.audiosegments,
            contexts=task.lyrics,
            languages=None,
            return_timestamps=True,
        )
        task.result = result
        return task


    def lyric_align(self, task: Task) -> Task:
        """"""
        self.log(
            task=task,
            stage="aligning",
            message="Aligning transcript to reference lyrics."
        )
        result, audiosegments = align2ref(
            task.result,
            task.lyrics,
            task.audiosegments,
            raise_if_not_reliable=False
        )
        task.result = result
        task.audiosegments = audiosegments
        return task
    

    def force_align(self, task: Task, aligner) -> Task:
        """"""
        self.log(
            task=task,
            stage="aligning",
            message="Running force alignment."
        )
        result = aligner.align(
            audio=task.audiopath,
            audiosegments=task.audiosegments,
            hypothesis=task.result.texts,
            languages=None,
        )
        result.to_line_idx(task.lyrics)
        task.result = result.populate_ass()
        return task
        

    def render(self, task: Task):
        """"""
        self.log(
            task=task,
            stage="rendering",
            message="Rendering karaoke output."
        )
        task.karaokepath = Render(
            with_ass=task.karaoke_type == 'plus'
        ).render(
            video_filepath=str(task.videopath),
            inst_path=str(task.instpath),
            duration=task.duration,
            result=task.result,
            output_path=None,
        )

        return task

    def upload(self, task: Task) -> Task:
        """"""
        self.log(
            task=task,
            stage="uploading",
            message="Uploading output."
        )
        return self.storage.upload(task)

    def _render_and_upload(self, task: Task) -> Task:
        """"""
        task = self.render(task)
        task = self.upload(task)

        return task

    def _filter_plus(self, tasks: list[Task]):
        """ Will yield non error and plus karaoke type
        """
        for task in tasks:
            if task.karaoke_type == "plus" and task.error is None:
                yield task

    def _fail_task(self, task: Task, exc: Exception, *, stage: PipelineStage) -> None:
        """
        """
        task.status = "error"
        task.error = {
            "type": type(exc),
            "message": str(exc),
            "traceback": "".join(traceback.format_exception(exc)),
        }

        self.log(
            task=task,
            stage=stage,
            message=str(exc),
            level="error",
        )

        logging.error(
            "Task %s failed:\n%s",
            task.id,
            traceback.format_exc(),
        )
    
    def run(self, tasks: list[Task]) -> list[Task]:
        """ Main Pipeline Entry for processing multiple tasks.
        """
        render_executor = ThreadPoolExecutor(max_workers=self.render_workers)
        render_futures = {}
        separator = None
        try:
            with ThreadPoolExecutor(
                max_workers=self.download_workers,
            ) as executor:
                futures = {executor.submit(self.download, task,): task
                    for task in tasks
                }
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        task = future.result()
                    except Exception as exc:
                        self._fail_task(task, exc, stage="downloading")
                    
                    if task.error is not None:
                        continue
                    
                    try:
                        if not separator:
                            self.log(
                                task=None,
                                stage="separating",
                                message="Loading Demucs model."
                            )
                            separator = BaseSeparator.from_options(
                                demucs="mdx_extra_q",
                                overlap=0.75,
                                segment=200,
                                shifts=1,
                                num_workers=0,
                            )
                        task = self.separate(task, separator)
                        if task.karaoke_type == "basic":
                            render_futures[
                                render_executor.submit(
                                    self._render_and_upload,
                                    task,
                                )
                            ] = task
                    except Exception as exc:
                        self._fail_task(task, exc, stage="separating")
            try:
                del separator.model, separator
            except:
                pass
            env.clean()

            # Detect Audio
            for task in self._filter_plus(tasks):
                try:
                    self.detect_audio_activity(task)
                except Exception as exc:
                    self._fail_task(task, exc, stage="detecting")

            # Transcribe
            transcriber = None
            for task in self._filter_plus(tasks):
                if task and not transcriber:
                    self.log(
                        task=None,
                        stage="transcribing",
                        message="Loading Qwen model."
                    )
                    transcriber: ASRMixin = HFModel.from_pretrained(
                        "Qwen/Qwen3-ASR-1.7B-hf",
                        max_inference_batch_size=1,
                        num_beams=4,
                    )
                try:
                    self.transcribe(task, transcriber)
                except Exception as exc:
                    self._fail_task(task, exc, stage="transcribing")
            try:
                del transcriber.model, transcriber
            except:
                pass
            env.clean()

            # Lyric Align
            for task in self._filter_plus(tasks):
                try:
                    self.lyric_align(task)
                except Exception as exc:
                    self._fail_task(task, exc, stage="aligning")

            # Force Align
            aligner = None
            for task in self._filter_plus(tasks):
                if task and not aligner: # Lazy Load
                    self.log(
                        task=None,
                        stage="aligning",
                        message="Loading MMS model."
                    )
                    aligner: ASRMixin = HFModel.from_pretrained("facebook/mms-1b-all",)
                try:
                    task = self.force_align(task, aligner)
                    render_futures[
                        render_executor.submit(
                            self._render_and_upload,
                            task,
                        )
                    ] = task
                except Exception as exc:
                    self._fail_task(task, exc, stage="aligning")
            try:
                del aligner.model, aligner.processor, aligner
            except:
                pass
            env.clean()

            for future in as_completed(render_futures):
                task = render_futures[future]
                try:
                    task = future.result()
                    self.log(
                        task=task,
                        stage="completed",
                        message="Task completed."
                    )
                except Exception as exc:
                    self._fail_task(task, exc, stage="rendering")

            render_executor.shutdown()

            self.cleanup(tasks)
            
            return tasks

    def cleanup(self, tasks) -> list[Task]:
        for task in tasks:
            for path in [
                task.karaokepath,
                task.videopath,
                task.instpath,
                task.audiopath,
            ]:
                if path is not None:
                    Path(path).unlink(
                        missing_ok=True,
                    )
            

class Worker:
    """ Main Worker Class
    """
    def __init__(
        self,
        cookiefile: str,
        api_url: str,
        api_token: str,
        worker_id: int,
        user_token: dict,
        root_folder_id: str,
        **kwargs
    ):
        self.api = IantirtaAPI(
            api_url=api_url,
            api_token=api_token,
            worker_id=worker_id,
            timeout=30.0,
        )
        self.log: Log = Log(
            self.api,
            flush_size=20,
            flush_interval=5.0,
        )
        self.storage = DriveStorage(
            user_token=user_token,
            root_folder_id=root_folder_id,
        )
        self.pipeline = Pipeline(
            cookiefile=cookiefile
            log=self.log,
            storage=self.storage,
            download_workers=5,
            render_workers=3,
        )

    def start(self):
        """ Start Worker
        """
        self.log(
            task=None,
            stage="queued",
            message="Worker started.",
        )
        try:
            while True:
                if not (tasks := self.api.claim_tasks()):
                    self.log(
                        task=None,
                        stage="completed",
                        message="No more tasks to process.",
                    )
                    break
                self.api.worker_start(tasks)
                self.log(
                    task=None,
                    stage="queued",
                    message=f"Claimed {len(tasks)} task(s).",
                )
                try:
                    tasks = self.pipeline.run(tasks)
                    self.api.finish_tasks(tasks)
                except Exception:
                    logger.exception("Pipeline batch failed.")
                    self.api.finish_tasks(tasks)
        finally:
            self.log.flush()
            try:
                self.api.worker_stop()
            except Exception:
                logging.exception(
                    "Failed to report worker shutdown."
                )
        

def main() -> None:
    """ Main Entry
        ## Note! this must be passed from backend:
        * str IANTIRTA_URL
        * str IANTIRTA_API_KEY
        * int WORKER_ID
        * dict DRIVE_USER_TOKEN
        * str DRIVE_ROOT_FOLDER_ID
    """
    worker = Worker(
        cookiefile="cookies.txt",
        api_url=IANTIRTA_URL,
        api_token=IANTIRTA_API_KEY,
        worker_id=WORKER_ID,
        user_token=DRIVE_USER_TOKEN,
        root_folder_id=DRIVE_ROOT_FOLDER_ID,
    )
    worker.start()


if __name__ == "__main__":
    karaoke_worker = KaraokeWorker(
        cookiefile="cookies.txt",
        api_url=IANTIRTA_URL,
        worker_name=WORKER_NAME,
        worker_provider=WORKER_PROVIDER,
        user_info=DRIVE_USER_TOKEN,
        root_folder_id=SHARED_ROOT_FOLDER_ID,
    )
    tasks: list[Task] = karaoke_worker.get_tasks()
    try:
        logger.debug(f"Processing {len(tasks)}...")
        karaoke_worker.post_worker(tasks)
        tasks = karaoke_worker.run_tasks(tasks)
    except:
        raise
    finally:
        logger.info("Complete: All tasks processed through pipeline.")
        logger.info("complete")
        karaoke_worker.post_tasks(tasks)
