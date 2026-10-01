"""Locate FFmpeg and choose an H.264 encoder: ``h264_nvenc`` when it really works, otherwise ``libx264``.

Stdlib only so the light CLI, the PyInstaller sidecar and ``scripts/*.py`` can all import it.

Lookup order for the FFmpeg binaries:
1. ``WHITEBOARD_FFMPEG_DIR`` (the Tauri shell sets it to the bundled ``ffmpeg`` resource folder);
2. a ``ffmpeg`` folder next to the frozen sidecar executable (installed app layout);
3. ``vendor/ffmpeg`` and ``app/src-tauri/resources/ffmpeg`` in the source tree (developer machines);
4. ``PATH``.

Encoder choice can be forced with ``WHITEBOARD_VIDEO_ENCODER=auto|nvenc|x264``.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from pathlib import Path
import os, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
EXE = ".exe" if os.name == "nt" else ""
ENCODER_ENV = "WHITEBOARD_VIDEO_ENCODER"
DIR_ENV = "WHITEBOARD_FFMPEG_DIR"
NVENC_ARGS = ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "23", "-b:v", "0", "-pix_fmt", "yuv420p"]
X264_ARGS = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"]

class FFmpegNotFound(RuntimeError):
    """Raised when no usable ffmpeg/ffprobe pair can be found."""

@dataclass(frozen=True)
class FFmpegTools:
    ffmpeg: str
    ffprobe: str | None
    source: str  # env | bundled | source-tree | path

@dataclass(frozen=True)
class VideoEncoder:
    name: str  # h264_nvenc | libx264
    args: list[str] = field(default_factory=list)
    hardware: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

def _candidate_dirs() -> list[tuple[str, Path]]:
    dirs: list[tuple[str, Path]] = []
    if os.environ.get(DIR_ENV):
        dirs.append(("env", Path(os.environ[DIR_ENV])))
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        dirs += [("bundled", exe_dir / "ffmpeg"), ("bundled", exe_dir / "resources" / "ffmpeg")]
    dirs += [("source-tree", ROOT / "vendor" / "ffmpeg"), ("source-tree", ROOT / "app" / "src-tauri" / "resources" / "ffmpeg")]
    return dirs

def find_ffmpeg(required: bool = True) -> FFmpegTools | None:
    for source, folder in _candidate_dirs():
        for base in (folder, folder / "bin"):
            ffmpeg = base / f"ffmpeg{EXE}"
            if ffmpeg.is_file():
                ffprobe = base / f"ffprobe{EXE}"
                return FFmpegTools(str(ffmpeg), str(ffprobe) if ffprobe.is_file() else None, source)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return FFmpegTools(ffmpeg, shutil.which("ffprobe"), "path")
    if required:
        raise FFmpegNotFound("FFmpeg not found. Reinstall the app, set WHITEBOARD_FFMPEG_DIR, or run tools/fetch_ffmpeg.py.")
    return None

def _run(cmd: list[str], timeout: float = 30) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)

_ENCODERS: dict[str, set[str]] = {}
_NVENC_OK: dict[str, bool] = {}

def list_encoders(ffmpeg: str) -> set[str]:
    if ffmpeg not in _ENCODERS:
        res = _run([ffmpeg, "-hide_banner", "-encoders"])
        names = set()
        for line in res.stdout.splitlines():
            match = re.match(r"\s*[VAS][A-Z.]{5}\s+(\S+)", line)
            if match:
                names.add(match.group(1))
        _ENCODERS[ffmpeg] = names
    return _ENCODERS[ffmpeg]

def nvenc_usable(ffmpeg: str) -> bool:
    """``h264_nvenc`` listed is not enough: it needs an NVIDIA driver/GPU, so encode one tiny frame to be sure."""
    if ffmpeg not in _NVENC_OK:
        ok = False
        if "h264_nvenc" in list_encoders(ffmpeg):
            try:
                res = _run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.2",
                            "-frames:v", "2", *NVENC_ARGS, "-f", "null", "-"], timeout=20)
                ok = res.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                ok = False
        _NVENC_OK[ffmpeg] = ok
    return _NVENC_OK[ffmpeg]

def h264_encoder_candidates(ffmpeg: str, prefer: str | None = None) -> list[VideoEncoder]:
    """Ordered encoders to try. ``prefer``: auto (default), nvenc or x264."""
    prefer = (prefer or os.environ.get(ENCODER_ENV) or "auto").lower()
    if prefer not in {"auto", "nvenc", "x264"}:
        raise ValueError(f"{ENCODER_ENV} must be auto, nvenc or x264, not {prefer!r}")
    x264 = VideoEncoder("libx264", list(X264_ARGS), False)
    nvenc = VideoEncoder("h264_nvenc", list(NVENC_ARGS), True)
    has_x264 = "libx264" in list_encoders(ffmpeg)
    out: list[VideoEncoder] = []
    if prefer != "x264" and nvenc_usable(ffmpeg):
        out.append(nvenc)
    if has_x264:
        out.append(x264)
    if not out:
        raise FFmpegNotFound(f"{ffmpeg} has neither a working h264_nvenc nor libx264")
    return out

def select_h264_encoder(ffmpeg: str | None = None, prefer: str | None = None) -> VideoEncoder:
    return h264_encoder_candidates(ffmpeg or find_ffmpeg().ffmpeg, prefer)[0]

def run_h264_encode(build_cmd, ffmpeg: str | None = None, prefer: str | None = None, log=print) -> tuple[subprocess.CompletedProcess, VideoEncoder]:
    """Run ``build_cmd(ffmpeg, encoder_args)`` with each candidate; NVENC failures (session limit, driver) fall back to libx264."""
    ffmpeg = ffmpeg or find_ffmpeg().ffmpeg
    last: subprocess.CompletedProcess | None = None
    candidates = h264_encoder_candidates(ffmpeg, prefer)
    for encoder in candidates:
        last = subprocess.run(build_cmd(ffmpeg, list(encoder.args)), capture_output=True, text=True, check=False)
        if last.returncode == 0:
            return last, encoder
        if log:
            log(f"  [warn] {encoder.name} failed: {last.stderr.strip()[-300:]}")
    assert last is not None
    return last, candidates[-1]

def ffmpeg_version(ffmpeg: str) -> dict:
    res = _run([ffmpeg, "-hide_banner", "-version"])
    first = res.stdout.splitlines()[0] if res.stdout else ""
    config = next((line for line in res.stdout.splitlines() if line.startswith("configuration:")), "")
    lic = "GPL-3.0-or-later" if "--enable-version3" in config and "--enable-gpl" in config else "GPL-2.0-or-later" if "--enable-gpl" in config else "LGPL"
    return {"version": first, "license": lic, "nonfree": "--enable-nonfree" in config}

def media_report(prefer: str | None = None) -> dict:
    tools = find_ffmpeg(required=False)
    if tools is None:
        return {"ffmpeg": None, "error": "FFmpeg not found", "encoder": None}
    encoders = list_encoders(tools.ffmpeg)
    try:
        selected = select_h264_encoder(tools.ffmpeg, prefer).to_dict()
    except (FFmpegNotFound, ValueError) as exc:
        selected = {"error": str(exc)}
    return {"ffmpeg": tools.ffmpeg, "ffprobe": tools.ffprobe, "source": tools.source, **ffmpeg_version(tools.ffmpeg),
            "hasLibx264": "libx264" in encoders, "hasNvencEncoder": "h264_nvenc" in encoders,
            "nvencUsable": nvenc_usable(tools.ffmpeg), "encoder": selected}
