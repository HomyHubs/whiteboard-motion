import tempfile,unittest
from pathlib import Path
from backend.models import ModelManager
from backend.models.manager import LicenseNotAccepted
from backend.hardware import NvidiaGpu
from backend.profiles import select_qwen_profile
from backend.providers.image.qwen_ncnn import QwenImage21NcnnProvider

class LowVramTests(unittest.TestCase):
 def test_8gb_profiles_use_ncnn(self):
  for name in ("NVIDIA GeForce RTX 4060","NVIDIA GeForce RTX 5060"):
   p=select_qwen_profile(NvidiaGpu(0,name,8192,"x","x")); self.assertEqual(p.backend,"ncnn-vulkan")
 def test_5060ti_16gb_uses_diffusers(self):
  p=select_qwen_profile(NvidiaGpu(0,"NVIDIA GeForce RTX 5060 Ti",16384,"x","x")); self.assertEqual(p.backend,"diffusers")
 def test_license_guard(self):
  with tempfile.TemporaryDirectory() as tmp:
   m=ModelManager(Path(tmp))
   with self.assertRaises(LicenseNotAccepted): m.download("qwen-image-2.1-ncnn")
   m.accept_license("qwen-image-2.1-ncnn"); self.assertTrue(m.is_license_accepted("qwen-image-2.1-ncnn"))
 def test_ncnn_validation_reports_missing(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp); (root/'runtime').mkdir(); (root/'runtime/qwenimage-ncnn-vulkan.exe').touch(); (root/'model').mkdir()
   state=QwenImage21NcnnProvider(root/'runtime',root/'model').validate(); self.assertFalse(state['ok']); self.assertEqual(len(state['missing']),3)
