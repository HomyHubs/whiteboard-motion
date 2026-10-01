import importlib.util,sys,unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('benchmark_qwen',Path(__file__).parents[2]/'tools/benchmark_qwen.py')
MOD=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MOD;SPEC.loader.exec_module(MOD)
class BenchmarkTests(unittest.TestCase):
 def test_parse_sizes(self):self.assertEqual(MOD.parse_sizes(['768x768','1024x1024']),[(768,768),(1024,1024)])
 def test_size_alignment(self):
  with self.assertRaises(ValueError):MOD.parse_sizes(['777x768'])
 def test_backend_override(self):
  from backend.hardware import NvidiaGpu
  from backend.profiles import select_qwen_profile
  profile=select_qwen_profile(NvidiaGpu(0,'NVIDIA GeForce RTX 5060 Ti',16384,'x','x'))
  self.assertEqual(profile.backend,'diffusers')
  self.assertEqual(MOD.with_backend(profile,'ncnn-vulkan').backend,'ncnn-vulkan')
 def test_preflight_ids(self):
  import tempfile
  from backend.models import ModelManager
  from backend.hardware import NvidiaGpu
  from backend.profiles import select_qwen_profile
  with tempfile.TemporaryDirectory() as tmp:
   profile=select_qwen_profile(NvidiaGpu(0,'NVIDIA GeForce RTX 3060',12288,'x','x'))
   check=MOD.preflight(profile,ModelManager(Path(tmp)))
   self.assertEqual([x['id'] for x in check['requiredModels']],['qwen-image-2.1-ncnn','qwenimage-ncnn-windows-runtime'])
