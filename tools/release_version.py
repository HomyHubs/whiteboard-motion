#!/usr/bin/env python3
"""Keep the app version identical in tauri.conf.json, Cargo.toml, package.json and backend/__init__.py.

  python tools/release_version.py check [--tag v0.2.0]   # CI: fail if files disagree or differ from the tag
  python tools/release_version.py set 0.2.0               # bump every file
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?"
FILES = {
    "app/src-tauri/tauri.conf.json": (r'("version"\s*:\s*")(' + SEMVER + r')(")', 1),
    "app/package.json": (r'("version"\s*:\s*")(' + SEMVER + r')(")', 1),
    "app/src-tauri/Cargo.toml": (r'(?m)^(version\s*=\s*")(' + SEMVER + r')(")', 1),
    "backend/__init__.py": (r'(__version__\s*=\s*")(' + SEMVER + r')(")', 1),
}

def read_versions(root: Path = ROOT) -> dict[str, str]:
    out = {}
    for rel, (pattern, _) in FILES.items():
        match = re.search(pattern, (root / rel).read_text(encoding="utf-8"))
        if not match:
            raise SystemExit(f"[err] version not found in {rel}")
        out[rel] = match.group(2)
    return out

def set_version(version: str, root: Path = ROOT) -> None:
    if not re.fullmatch(SEMVER, version):
        raise SystemExit(f"[err] not a semver version: {version}")
    for rel, (pattern, count) in FILES.items():
        path = root / rel
        text = re.sub(pattern, lambda m: m.group(1) + version + m.group(3), path.read_text(encoding="utf-8"), count=count)
        path.write_text(text, encoding="utf-8")
    if (root / "app/package-lock.json").is_file():
        lock = json.loads((root / "app/package-lock.json").read_text(encoding="utf-8"))
        lock["version"] = version
        if "" in lock.get("packages", {}):
            lock["packages"][""]["version"] = version
        (root / "app/package-lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")

def main(argv=None) -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--tag")
    s = sub.add_parser("set"); s.add_argument("version")
    a = p.parse_args(argv)
    if a.cmd == "set":
        set_version(a.version.lstrip("v")); print(f"VERSION={a.version.lstrip('v')}"); return 0
    versions = read_versions(); unique = set(versions.values())
    if len(unique) != 1:
        print("[err] versions differ: " + json.dumps(versions, indent=2), file=sys.stderr); return 1
    version = unique.pop()
    if a.tag and a.tag.lstrip("v") != version:
        print(f"[err] tag {a.tag} != app version {version}", file=sys.stderr); return 1
    print(f"VERSION={version}"); print(f"PRERELEASE={'true' if '-' in version else 'false'}"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
