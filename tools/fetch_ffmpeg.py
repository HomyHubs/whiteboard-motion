#!/usr/bin/env python3
"""Download the pinned Windows FFmpeg build, verify SHA-256 and stage it for the Tauri bundle.

Output: app/src-tauri/resources/ffmpeg/{ffmpeg.exe, ffprobe.exe, LICENSE.txt, BUILD-README.txt, NOTICE.txt, ffmpeg-bundle.json}
Usage:  python tools/fetch_ffmpeg.py [--dest DIR] [--archive LOCAL_ZIP] [--force]
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "ffmpeg-manifest.json"
DEFAULT_DEST = ROOT / "app" / "src-tauri" / "resources" / "ffmpeg"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def notice(m: dict) -> str:
    src = m["sourceCode"]
    return (f"Whiteboard Video bundles FFmpeg {m['build']} as separate programs (ffmpeg.exe, ffprobe.exe).\n"
            f"They are licensed under {m['license']}; see LICENSE.txt. The application itself is MIT licensed\n"
            "and only runs these programs as external processes.\n\n"
            "Corresponding source code:\n"
            f"  FFmpeg:        {src['ffmpeg']}\n  Release:       {src['ffmpegRelease']}\n"
            f"  Build scripts: {src['buildScripts']}\n  x264:          {src['libx264']}\n\n"
            f"Original archive: {m['url']}\nSHA-256: {m['sha256']}\n"
            "Written offer: for three years from distribution we provide the exact corresponding source on request\n"
            "via https://github.com/HomyHubs/whiteboard-motion/issues.\n")

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    p.add_argument("--archive", type=Path, help="use an already downloaded zip (still SHA-256 checked)")
    p.add_argument("--force", action="store_true")
    a = p.parse_args(argv)
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stamp = a.dest / "ffmpeg-bundle.json"
    if stamp.is_file() and not a.force:
        current = json.loads(stamp.read_text(encoding="utf-8"))
        if current.get("sha256") == m["sha256"] and all((a.dest / name).is_file() for name in m["files"].values()):
            print(f"FFMPEG_DIR={a.dest} (up to date)"); return 0
    with tempfile.TemporaryDirectory() as tmp:
        archive = a.archive
        if archive is None:
            archive = Path(tmp) / "ffmpeg.zip"
            print(f"Downloading {m['url']} ({m['sizeBytes'] / 1e6:.0f} MB)")
            with urllib.request.urlopen(m["url"], timeout=120) as r, archive.open("wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        digest = sha256(archive)
        if digest != m["sha256"]:
            print(f"[err] SHA-256 mismatch: {digest} != {m['sha256']}", file=sys.stderr); return 2
        staging = Path(tmp) / "stage"; staging.mkdir()
        with zipfile.ZipFile(archive) as z:
            for inner, name in m["files"].items():
                with z.open(f"{m['archiveRoot']}/{inner}") as src, (staging / name).open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        (staging / "NOTICE.txt").write_text(notice(m), encoding="utf-8")
        files = {name: sha256(staging / name) for name in sorted(p.name for p in staging.iterdir())}
        (staging / "ffmpeg-bundle.json").write_text(json.dumps({"version": m["version"], "build": m["build"], "license": m["license"],
            "sha256": m["sha256"], "files": files}, indent=2), encoding="utf-8")
        if a.dest.exists():
            shutil.rmtree(a.dest)
        a.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staging, a.dest)
    print(f"FFMPEG_DIR={a.dest}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
