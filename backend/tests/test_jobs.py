import tempfile, time, unittest
from pathlib import Path
from backend.jobs import JobManager, JobCancelled

class JobTests(unittest.TestCase):
    def wait(self, manager, job_id, timeout=3):
        until = time.time() + timeout
        while time.time() < until:
            job = manager.get(job_id)
            if job.status in {"completed", "failed", "cancelled"}: return job
            time.sleep(.01)
        self.fail("job timeout")
    def test_progress_and_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = JobManager(2, Path(tmp)/"gpu.lock")
            job = m.submit("test", lambda ctx: (ctx.report(.5, "half"), "ok")[1])
            done = self.wait(m, job.id); m.shutdown()
            self.assertEqual((done.status, done.result, done.progress), ("completed", "ok", 1.0))
    def test_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = JobManager(1, Path(tmp)/"gpu.lock")
            def work(ctx):
                for _ in range(200): time.sleep(.005); ctx.check_cancelled()
            job = m.submit("cancel", work); time.sleep(.03); self.assertTrue(m.cancel(job.id))
            done = self.wait(m, job.id); m.shutdown()
            self.assertEqual(done.status, "cancelled")
    def test_gpu_jobs_are_serialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = JobManager(2, Path(tmp)/"gpu.lock"); active = 0; peak = 0
            def work(ctx):
                nonlocal active, peak
                active += 1; peak = max(peak, active); time.sleep(.08); active -= 1
            a = m.submit("gpu-a", work, True); b = m.submit("gpu-b", work, True)
            self.wait(m, a.id); self.wait(m, b.id); m.shutdown()
            self.assertEqual(peak, 1)
