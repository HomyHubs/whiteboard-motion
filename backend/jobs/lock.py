from __future__ import annotations
import os, time
from pathlib import Path

class InterProcessFileLock:
    """One-byte advisory lock, compatible with Windows and Unix.

    The file is intentionally retained: lock ownership belongs to the OS handle,
    so a crashed process releases it automatically.
    """
    def __init__(self, path: Path, poll_seconds: float = 0.05):
        self.path, self.poll_seconds, self._file = path, poll_seconds, None

    def acquire(self, timeout: float | None = None) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.path, "a+b")
        self._file.seek(0)
        if self._file.read(1) == b"":
            self._file.write(b"0"); self._file.flush()
        started = time.monotonic()
        while True:
            try:
                self._file.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (OSError, BlockingIOError):
                if timeout is not None and time.monotonic() - started >= timeout:
                    self._file.close(); self._file = None
                    return False
                time.sleep(self.poll_seconds)

    def release(self) -> None:
        if not self._file: return
        try:
            self._file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        finally:
            self._file.close(); self._file = None

    def __enter__(self):
        if not self.acquire(): raise TimeoutError(f"Cannot acquire {self.path}")
        return self
    def __exit__(self, *_): self.release()
