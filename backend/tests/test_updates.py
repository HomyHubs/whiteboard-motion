import io, json, os, unittest
from unittest import mock
from backend import updates

RELEASE = {"tag_name": "v0.2.0", "html_url": "https://github.com/x/y/releases/tag/v0.2.0", "published_at": "2026-10-01T00:00:00Z",
           "assets": [{"name": "Whiteboard Video_0.2.0_x64-setup.exe", "browser_download_url": "https://e/setup.exe"},
                      {"name": "Whiteboard Video_0.2.0_x64_en-US.msi", "browser_download_url": "https://e/a.msi"},
                      {"name": "SHA256SUMS.txt", "browser_download_url": "https://e/SHA256SUMS.txt"}]}

class UpdateTests(unittest.TestCase):
    def test_versions(self):
        self.assertTrue(updates.is_newer("v0.2.0", "0.1.0"))
        self.assertFalse(updates.is_newer("0.1.0", "0.1.0"))
        self.assertTrue(updates.is_newer("0.2.0", "0.2.0-rc.1"))
        self.assertFalse(updates.is_newer("0.1.9", "0.2.0"))
        with self.assertRaises(ValueError): updates.parse_version("latest")
    def test_summary(self):
        s = updates.summarize_release(RELEASE, "0.1.0")
        self.assertEqual((s["latest"], s["updateAvailable"], s["installerUrl"]), ("0.2.0", True, "https://e/setup.exe"))
        self.assertEqual(s["sha256SumsUrl"], "https://e/SHA256SUMS.txt")
    def test_check_uses_network_only_when_called(self):
        resp = mock.MagicMock(); resp.__enter__.return_value = io.BytesIO(json.dumps(RELEASE).encode())
        with mock.patch.object(updates.urllib.request, "urlopen", return_value=resp) as urlopen:
            self.assertEqual(updates.check_for_update()["latest"], "0.2.0")
        urlopen.assert_called_once()
    def test_offline_is_not_an_exception(self):
        with mock.patch.object(updates.urllib.request, "urlopen", side_effect=updates.urllib.error.URLError("offline")):
            r = updates.check_for_update()
        self.assertFalse(r["updateAvailable"]); self.assertIn("error", r)
    def test_disabled(self):
        with mock.patch.dict(os.environ, {updates.DISABLE_ENV: "1"}):
            self.assertTrue(updates.check_for_update()["disabled"])
