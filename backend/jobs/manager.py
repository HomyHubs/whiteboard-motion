from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import threading, traceback, uuid
from pathlib import Path
from typing import Any, Callable
from .lock import InterProcessFileLock
from ..config import app_data_dir

class JobCancelled(RuntimeError): pass

def utc_now() -> str: return datetime.now(timezone.utc).isoformat()

@dataclass
class JobRecord:
    id: str
    kind: str
    uses_gpu: bool
    status: str = "queued"
    progress: float = 0.0
    message: str = ""
    result: Any = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    cancel_requested: bool = False
    def to_dict(self) -> dict: return asdict(self)

class JobContext:
    def __init__(self, record: JobRecord, cancel: threading.Event, on_change: Callable[[], None]):
        self.record, self._cancel, self._on_change = record, cancel, on_change
    def check_cancelled(self) -> None:
        if self._cancel.is_set(): raise JobCancelled("Job cancelled")
    def report(self, progress: float, message: str = "") -> None:
        self.check_cancelled()
        self.record.progress = max(0.0, min(1.0, float(progress)))
        self.record.message = message
        self._on_change()

JobFunction = Callable[[JobContext], Any]

class JobManager:
    def __init__(self, max_workers: int = 4, gpu_lock_path: Path | None = None):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="whiteboard-job")
        self._records: dict[str, JobRecord] = {}
        self._cancel: dict[str, threading.Event] = {}
        self._guard = threading.RLock()
        self.gpu_lock_path = gpu_lock_path or app_data_dir() / "locks" / "gpu.lock"

    def submit(self, kind: str, function: JobFunction, uses_gpu: bool = False) -> JobRecord:
        job_id = uuid.uuid4().hex
        record = JobRecord(job_id, kind, uses_gpu)
        with self._guard:
            self._records[job_id] = record; self._cancel[job_id] = threading.Event()
        self._executor.submit(self._run, record, function)
        return record

    def _run(self, record: JobRecord, function: JobFunction) -> None:
        event = self._cancel[record.id]
        context = JobContext(record, event, lambda: None)
        lock = InterProcessFileLock(self.gpu_lock_path) if record.uses_gpu else None
        try:
            if event.is_set(): raise JobCancelled("Job cancelled before start")
            record.status = "waiting_gpu" if lock else "running"
            if lock: lock.acquire()
            context.check_cancelled()
            record.status, record.started_at = "running", utc_now()
            record.result = function(context)
            context.check_cancelled()
            record.status, record.progress = "completed", 1.0
        except JobCancelled as exc:
            record.status, record.message = "cancelled", str(exc)
        except Exception as exc:
            record.status, record.error = "failed", f"{type(exc).__name__}: {exc}"
            record.message = traceback.format_exc(limit=5)
        finally:
            if lock: lock.release()
            record.finished_at = utc_now()

    def cancel(self, job_id: str) -> bool:
        with self._guard:
            record = self._records.get(job_id)
            if not record or record.status in {"completed", "failed", "cancelled"}: return False
            record.cancel_requested = True; self._cancel[job_id].set(); return True

    def get(self, job_id: str) -> JobRecord | None:
        with self._guard: return self._records.get(job_id)
    def list(self) -> list[JobRecord]:
        with self._guard: return sorted(self._records.values(), key=lambda x: x.created_at, reverse=True)
    def shutdown(self, wait: bool = True) -> None: self._executor.shutdown(wait=wait, cancel_futures=True)
