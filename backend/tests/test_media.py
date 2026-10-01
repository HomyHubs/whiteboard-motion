import os, shutil, subprocess, tempfile, unittest
from pathlib import Path
from unittest import mock
from backend.media import ffmpeg as media

class FakeRun:
    """Simulates ffmpeg: encoder list and whether an NVENC test encode works."""
    def __init__(self, encoders, nvenc_works):
        self.encoders, self.nvenc_works = encoders, nvenc_works
    def __call__(self, cmd, timeout=30):
        if "-encoders" in cmd:
            out = "\n".join(f" V....D {name}  desc" for name in self.encoders)
            return subprocess.CompletedProcess(cmd, 0, out, "")
        if "h264_nvenc" in cmd:
            return subprocess.CompletedProcess(cmd, 0 if self.nvenc_works else 1, "", "" if self.nvenc_works else "No capable devices found")
        return subprocess.CompletedProcess(cmd, 0, "ffmpeg version 9\nconfiguration: --enable-gpl --enable-version3", "")

class MediaTests(unittest.TestCase):
    def setUp(self):
        media._ENCODERS.clear(); media._NVENC_OK.clear()
        self.env = mock.patch.dict(os.environ, {}, clear=False); self.env.start(); os.environ.pop(media.ENCODER_ENV, None)
    def tearDown(self):
        self.env.stop(); media._ENCODERS.clear(); media._NVENC_OK.clear()
    def test_nvenc_preferred_when_usable(self):
        with mock.patch.object(media, "_run", FakeRun({"libx264", "h264_nvenc"}, True)):
            names = [e.name for e in media.h264_encoder_candidates("ff")]
        self.assertEqual(names, ["h264_nvenc", "libx264"])
    def test_no_gpu_falls_back_to_libx264(self):
        # Gyan build lists h264_nvenc even on machines without NVIDIA; test encode fails -> libx264.
        with mock.patch.object(media, "_run", FakeRun({"libx264", "h264_nvenc"}, False)):
            self.assertEqual(media.select_h264_encoder("ff").name, "libx264")
            self.assertFalse(media.nvenc_usable("ff"))
    def test_force_x264(self):
        with mock.patch.object(media, "_run", FakeRun({"libx264", "h264_nvenc"}, True)):
            self.assertEqual(media.select_h264_encoder("ff", prefer="x264").name, "libx264")
    def test_invalid_preference(self):
        with mock.patch.object(media, "_run", FakeRun({"libx264"}, False)), self.assertRaises(ValueError):
            media.h264_encoder_candidates("ff", prefer="vp9")
    def test_no_h264_encoder(self):
        with mock.patch.object(media, "_run", FakeRun({"mpeg4"}, False)), self.assertRaises(media.FFmpegNotFound):
            media.select_h264_encoder("ff")
    def test_runtime_nvenc_failure_retries_libx264(self):
        calls = []
        def fake_subprocess_run(cmd, **kw):
            calls.append(cmd); ok = "libx264" in cmd
            return subprocess.CompletedProcess(cmd, 0 if ok else 1, "", "" if ok else "OpenEncodeSessionEx failed")
        with mock.patch.object(media, "_run", FakeRun({"libx264", "h264_nvenc"}, True)), \
             mock.patch.object(media.subprocess, "run", fake_subprocess_run):
            res, enc = media.run_h264_encode(lambda ff, args: [ff, *args, "out.mp4"], ffmpeg="ff", log=None)
        self.assertEqual((res.returncode, enc.name, len(calls)), (0, "libx264", 2))
    def test_env_dir_has_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("ffmpeg", "ffprobe"):
                (Path(tmp) / f"{name}{media.EXE}").write_bytes(b"")
            with mock.patch.dict(os.environ, {media.DIR_ENV: tmp}):
                tools = media.find_ffmpeg()
        self.assertEqual((tools.source, Path(tools.ffmpeg).parent), ("env", Path(tmp)))
    def test_frozen_bundled_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "ffmpeg").mkdir(); (Path(tmp) / "ffmpeg" / f"ffmpeg{media.EXE}").write_bytes(b"")
            with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(media.sys, "frozen", True, create=True), \
                 mock.patch.object(media.sys, "executable", str(Path(tmp) / "whiteboard-backend.exe")):
                os.environ.pop(media.DIR_ENV, None)
                tools = media.find_ffmpeg()
        self.assertEqual(tools.source, "bundled")
    def test_missing_ffmpeg(self):
        with mock.patch.object(media, "_candidate_dirs", lambda: []), mock.patch.object(media.shutil, "which", lambda _: None):
            self.assertIsNone(media.find_ffmpeg(required=False))
            self.assertIsNone(media.media_report()["ffmpeg"])
            with self.assertRaises(media.FFmpegNotFound): media.find_ffmpeg()

@unittest.skipUnless(shutil.which("ffmpeg"), "system ffmpeg not installed")
class RealFFmpegTests(unittest.TestCase):
    def test_real_encode_with_selected_encoder(self):
        media._ENCODERS.clear(); media._NVENC_OK.clear()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "t.mp4"
            res, enc = media.run_h264_encode(lambda ff, args: [ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                                             "testsrc2=s=320x180:d=1:r=10", *args, str(out)], log=None)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue(out.stat().st_size > 0)
            self.assertIn(enc.name, {"libx264", "h264_nvenc"})
