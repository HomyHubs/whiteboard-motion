import tempfile,time,unittest
from pathlib import Path
from backend.jobs import JobManager
from backend.services.model_jobs import submit_model_download
class FakeManager:
 def entry(self,model_id):return {'id':model_id}
 def download(self,model_id):return Path('/models')/model_id
class ModelJobTests(unittest.TestCase):
 def test_download_job(self):
  with tempfile.TemporaryDirectory() as tmp:
   jobs=JobManager(1,Path(tmp)/'gpu.lock');job=submit_model_download(FakeManager(),jobs,'model')
   for _ in range(100):
    current=jobs.get(job.id)
    if current.status in {'completed','failed'}:break
    time.sleep(.01)
   jobs.shutdown();self.assertEqual(current.status,'completed');self.assertEqual(current.result['modelId'],'model')
