import importlib.util,sys,unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('benchmark_voxcpm',Path(__file__).parents[2]/'tools/benchmark_voxcpm.py');MOD=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MOD;SPEC.loader.exec_module(MOD)
class VoiceBenchmarkTests(unittest.TestCase):
 def test_rtf(self):self.assertEqual(MOD.rtf(2,4),.5)
 def test_rtf_zero(self):self.assertIsNone(MOD.rtf(2,0))
