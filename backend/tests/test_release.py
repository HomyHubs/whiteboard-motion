import importlib.util, json, shutil, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release_version", ROOT / "tools" / "release_version.py")
rv = importlib.util.module_from_spec(spec); spec.loader.exec_module(rv)

class ReleaseTests(unittest.TestCase):
    def test_repo_versions_in_sync(self):
        self.assertEqual(len(set(rv.read_versions().values())), 1)
    def test_set_version_updates_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in list(rv.FILES) + ["app/package-lock.json"]:
                (root / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(ROOT / rel, root / rel)
            rv.set_version("0.2.0-rc.1", root)
            self.assertEqual(set(rv.read_versions(root).values()), {"0.2.0-rc.1"})
            self.assertEqual(json.loads((root / "app/package-lock.json").read_text())["version"], "0.2.0-rc.1")
            cargo = (root / "app/src-tauri/Cargo.toml").read_text()
            self.assertIn('tauri = { version = "2"', cargo)  # dependency versions untouched
    def test_tauri_bundles_ffmpeg_and_icons(self):
        conf = json.loads((ROOT / "app/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
        self.assertEqual(conf["bundle"]["resources"], {"resources/ffmpeg/": "ffmpeg/"})
        for icon in conf["bundle"]["icon"]:
            self.assertTrue((ROOT / "app/src-tauri" / icon).is_file(), icon)
    def test_ffmpeg_manifest_pinned(self):
        m = json.loads((ROOT / "tools/ffmpeg-manifest.json").read_text())
        self.assertRegex(m["sha256"], r"^[0-9a-f]{64}$"); self.assertIn("/releases/download/", m["url"])
        self.assertTrue(m["license"].startswith("GPL")); self.assertIn("ffmpeg", m["sourceCode"])
