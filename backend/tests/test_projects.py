import tempfile,unittest
from pathlib import Path
from backend.projects import ProjectStore,InvalidProjectId
class ProjectTests(unittest.TestCase):
 def test_create_save_load(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=ProjectStore(Path(tmp));project=store.create('My Video');store.save_scene(project['id'],'scene-01',{'canvas':{'width':100,'height':100}});loaded=store.get(project['id']);self.assertEqual(loaded['scenes'],['scene-01']);self.assertEqual(store.load_scene(project['id'],'scene-01')['sceneId'],'scene-01')
 def test_path_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=ProjectStore(Path(tmp))
   with self.assertRaises(InvalidProjectId):store.path('../secret')
 def test_atomic_no_tmp_left(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=ProjectStore(Path(tmp));store.create('Demo');self.assertEqual(list(Path(tmp).rglob('*.tmp')),[])
