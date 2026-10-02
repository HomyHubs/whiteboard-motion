import json, threading, unittest, urllib.request, urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path
from backend.server import Handler

class ServerVoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_get_voices(self):
        req = urllib.request.Request(self._url("/voices"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsInstance(data, list)
            ids = [v["id"] for v in data]
            self.assertIn("vi-standard", ids)

    def test_post_voice_without_consent_fails(self):
        body = json.dumps({
            "id": "clone-fail",
            "name": "Clone Fail",
            "isClone": True,
            "referenceAudio": "nonexistent.wav",
            "consentConfirmed": False,
        }).encode("utf-8")
        req = urllib.request.Request(self._url("/voices"), data=body, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)

    def test_post_custom_tts_and_delete(self):
        body = json.dumps({
            "id": "server-tts-test",
            "name": "Server Test TTS",
            "language": "en",
            "isClone": False,
        }).encode("utf-8")
        req = urllib.request.Request(self._url("/voices"), data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["id"], "server-tts-test")

        # Get voice details
        req_get = urllib.request.Request(self._url("/voices/server-tts-test"))
        with urllib.request.urlopen(req_get) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["name"], "Server Test TTS")

        # Delete voice
        req_del = urllib.request.Request(self._url("/voices/server-tts-test"), method="DELETE")
        with urllib.request.urlopen(req_del) as resp:
            self.assertEqual(resp.status, 200)

    def test_get_audit_log(self):
        req = urllib.request.Request(self._url("/audit/voice-clones?limit=5"))
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIsInstance(data, list)
