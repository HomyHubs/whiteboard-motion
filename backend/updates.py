"""Manual update check against GitHub Releases. Never downloads or installs anything by itself."""
from __future__ import annotations
import json, os, re, urllib.error, urllib.request
from . import __version__

DEFAULT_URL = "https://api.github.com/repos/HomyHubs/whiteboard-motion/releases/latest"
URL_ENV = "WHITEBOARD_UPDATE_URL"
DISABLE_ENV = "WHITEBOARD_DISABLE_UPDATE_CHECK"

def parse_version(text: str) -> tuple[tuple[int, int, int], str]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", text.strip())
    if not match:
        raise ValueError(f"Invalid version: {text!r}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3))), match.group(4) or ""

def is_newer(latest: str, current: str) -> bool:
    (lc, lp), (cc, cp) = parse_version(latest), parse_version(current)
    if lc != cc:
        return lc > cc
    return bool(cp) and not lp  # 0.2.0 > 0.2.0-rc.1; prereleases otherwise not compared

def summarize_release(release: dict, current: str = __version__) -> dict:
    tag = str(release.get("tag_name", ""))
    assets = {a.get("name", ""): a.get("browser_download_url") for a in release.get("assets", [])}
    installer = next((url for name, url in assets.items() if name.endswith("-setup.exe")), None) \
        or next((url for name, url in assets.items() if name.endswith(".msi")), None)
    return {"current": current, "latest": tag.lstrip("v"), "updateAvailable": is_newer(tag, current),
            "releaseUrl": release.get("html_url"), "installerUrl": installer, "sha256SumsUrl": assets.get("SHA256SUMS.txt"),
            "publishedAt": release.get("published_at"), "notes": (release.get("body") or "")[:4000]}

def check_for_update(url: str | None = None, timeout: float = 6.0) -> dict:
    if os.environ.get(DISABLE_ENV) == "1":
        return {"current": __version__, "disabled": True, "updateAvailable": False}
    request = urllib.request.Request(url or os.environ.get(URL_ENV) or DEFAULT_URL,
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": f"WhiteboardVideo/{__version__}"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            release = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"current": __version__, "latest": None, "updateAvailable": False, "error": "Chưa có bản phát hành nào."}
        return {"current": __version__, "updateAvailable": False, "error": f"HTTP {exc.code}: kiểm tra lại sau."}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"current": __version__, "updateAvailable": False, "error": f"Không kết nối được máy chủ cập nhật: {exc}"}
    return summarize_release(release)
