import json, tempfile, unittest
from pathlib import Path
from backend.security.audit import (
    DEFAULT_VOICE_CONSENT_STATEMENT,
    file_sha256,
    record_consent_event,
    record_synthesis_event,
    get_voice_audit_log,
)

class AuditTests(unittest.TestCase):
    def test_file_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sample.wav"
            p.write_bytes(b"RIFFdummydata")
            h = file_sha256(p)
            self.assertIsNotNone(h)
            self.assertEqual(len(h), 64)
            self.assertIsNone(file_sha256(Path(tmp) / "missing.wav"))

    def test_record_consent_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref_audio = root / "reference.wav"
            ref_audio.write_bytes(b"test audio sample")

            rec = record_consent_event(
                voice_id="speaker-1",
                name="Speaker One",
                reference_audio=ref_audio,
                reference_text="hello world",
                root=root,
            )
            self.assertEqual(rec["event"], "voice_clone_consent_granted")
            self.assertEqual(rec["voice_id"], "speaker-1")
            self.assertTrue(rec["consent_confirmed"])
            self.assertEqual(rec["statement"], DEFAULT_VOICE_CONSENT_STATEMENT)
            self.assertIsNotNone(rec["reference_audio_sha256"])

            # Verify in file
            log_file = root / "audit" / "voice_clones.jsonl"
            self.assertTrue(log_file.is_file())
            lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").strip().splitlines()]
            self.assertEqual(len(lines), 1)
            self.assertEqual(lines[0]["id"], rec["id"])

    def test_record_synthesis_event_and_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref_audio = root / "ref.wav"
            ref_audio.write_bytes(b"reference content")
            out_audio = root / "output.wav"
            out_audio.write_bytes(b"output content")

            rec = record_synthesis_event(
                output_audio=out_audio,
                reference_audio=ref_audio,
                text="Xin chao Viet Nam",
                model_revision="rev-123",
                language="vi",
                consent_confirmed=True,
                root=root,
            )
            self.assertEqual(rec["event"], "voice_clone_synthesized")
            self.assertTrue(rec["consent_confirmed"])

            # Sidecar check
            sidecar = out_audio.with_suffix(".wav.audit.json")
            self.assertTrue(sidecar.is_file())
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(data["auditSchema"], "whiteboard.voice-audit.v1")
            self.assertEqual(data["engine"], "voxcpm2")
            self.assertEqual(data["voiceType"], "voice-clone")
            self.assertTrue(data["consentConfirmed"])
            self.assertEqual(data["modelRevision"], "rev-123")

    def test_get_voice_audit_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref_audio = root / "ref.wav"
            ref_audio.write_bytes(b"sample")
            out_audio = root / "out.wav"
            out_audio.write_bytes(b"output")

            record_consent_event("spk1", "Speaker 1", ref_audio, root=root)
            record_synthesis_event(out_audio, ref_audio, "text 1", "rev", consent_confirmed=True, root=root)
            record_synthesis_event(out_audio, None, "text 2", "rev", consent_confirmed=False, root=root)

            all_logs = get_voice_audit_log(root=root)
            self.assertEqual(len(all_logs), 3)

            clone_synth = get_voice_audit_log(event_type="voice_clone_synthesized", root=root)
            self.assertEqual(len(clone_synth), 1)
            self.assertEqual(clone_synth[0]["event"], "voice_clone_synthesized")

            limited = get_voice_audit_log(limit=2, root=root)
            self.assertEqual(len(limited), 2)
