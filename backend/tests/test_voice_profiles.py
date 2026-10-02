import tempfile, unittest
from pathlib import Path
from backend.voices import VoiceProfileStore, InvalidVoiceId
from backend.security.audit import get_voice_audit_log

class VoiceProfileTests(unittest.TestCase):
    def test_builtin_voices_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VoiceProfileStore(root=Path(tmp))
            voices = store.list()
            ids = [v["id"] for v in voices]
            self.assertIn("vi-standard", ids)
            self.assertIn("en-standard", ids)

            vi = store.get("vi-standard")
            self.assertEqual(vi["language"], "vi")
            self.assertFalse(vi["isClone"])

            # Cannot delete built-in voice
            with self.assertRaises(ValueError):
                store.delete("vi-standard")

    def test_create_custom_tts_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VoiceProfileStore(root=Path(tmp))
            created = store.create(
                voice_id="my-tts",
                name="Custom TTS Voice",
                language="vi",
                is_clone=False,
            )
            self.assertEqual(created["id"], "my-tts")
            self.assertFalse(created["isClone"])

            got = store.get("my-tts")
            self.assertEqual(got["name"], "Custom TTS Voice")

    def test_clone_voice_requires_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = VoiceProfileStore(root=root / "voices")
            sample = root / "sample.wav"
            sample.write_bytes(b"RIFFdummyvoice")

            # Missing consent_confirmed
            with self.assertRaises(PermissionError):
                store.create(
                    voice_id="my-clone",
                    name="My Clone Voice",
                    language="vi",
                    is_clone=True,
                    reference_audio=sample,
                    reference_text="sample text",
                    consent_confirmed=False,
                )

    def test_clone_voice_requires_existing_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = VoiceProfileStore(root=root / "voices")
            missing = root / "nonexistent.wav"

            with self.assertRaises(FileNotFoundError):
                store.create(
                    voice_id="my-clone",
                    name="My Clone Voice",
                    language="vi",
                    is_clone=True,
                    reference_audio=missing,
                    reference_text="sample text",
                    consent_confirmed=True,
                )

    def test_clone_voice_success_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = VoiceProfileStore(root=root / "voices")
            sample = root / "sample.wav"
            sample.write_bytes(b"RIFFvalidvoiceaudio")

            created = store.create(
                voice_id="speaker-nam",
                name="Giọng Đọc Nam",
                language="vi",
                is_clone=True,
                reference_audio=sample,
                reference_text="Xin chào các bạn",
                consent_confirmed=True,
                consent_statement="Tôi cam kết sở hữu bản quyền giọng nói này",
            )
            self.assertTrue(created["isClone"])
            self.assertTrue(created["consentConfirmed"])
            self.assertIsNotNone(created["referenceAudioSha256"])
            self.assertIsNotNone(created["consentTimestamp"])

            # Verify audit trail
            logs = get_voice_audit_log(root=root)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["event"], "voice_clone_consent_granted")
            self.assertEqual(logs[0]["voice_id"], "speaker-nam")

            # Delete custom voice
            self.assertTrue(store.delete("speaker-nam"))
            with self.assertRaises(KeyError):
                store.get("speaker-nam")

    def test_invalid_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = VoiceProfileStore(root=Path(tmp))
            with self.assertRaises(InvalidVoiceId):
                store.create(voice_id="../../malicious", name="Bad")
            with self.assertRaises(InvalidVoiceId):
                store.create(voice_id="UPPERCASE_NOT_ALLOWED", name="Bad")
            with self.assertRaises(InvalidVoiceId):
                store.create(voice_id="voice@#$", name="Bad")
