"""FFmpeg helpers for the stand-alone scripts.

Uses ``backend.media`` (bundled FFmpeg lookup + h264_nvenc → libx264 fallback) when the repo backend is importable,
otherwise falls back to ``ffmpeg``/``ffprobe`` on PATH with libx264.
"""
from __future__ import annotations
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from backend.media import find_ffmpeg, run_h264_encode
except ImportError:  # scripts copied without the backend package
    find_ffmpeg = None
    run_h264_encode = None

_X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"]

def ffmpeg_bin() -> str | None:
    if find_ffmpeg is not None:
        tools = find_ffmpeg(required=False)
        return tools.ffmpeg if tools else None
    return shutil.which("ffmpeg")

def ffprobe_bin() -> str | None:
    if find_ffmpeg is not None:
        tools = find_ffmpeg(required=False)
        return tools.ffprobe if tools else None
    return shutil.which("ffprobe")

def encode_h264(build_cmd, log=print) -> tuple[subprocess.CompletedProcess | None, str | None]:
    """``build_cmd(ffmpeg, encoder_args) -> argv``. Returns (result, encoder name); (None, None) without FFmpeg."""
    ffmpeg = ffmpeg_bin()
    if ffmpeg is None:
        return None, None
    if run_h264_encode is not None:
        try:
            res, encoder = run_h264_encode(build_cmd, ffmpeg=ffmpeg, log=log)
            return res, encoder.name
        except (RuntimeError, ValueError) as exc:  # FFmpegNotFound / bad WHITEBOARD_VIDEO_ENCODER
            if log:
                log(f"  [warn] {exc}; using libx264")
    res = subprocess.run(build_cmd(ffmpeg, list(_X264)), capture_output=True, text=True, check=False)
    return res, "libx264"
