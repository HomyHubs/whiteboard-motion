import importlib.util,sys,unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('benchmark_qwen',Path(__file__).parents[2]/'tools/benchmark_qwen.py')
MOD=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MOD;SPEC.loader.exec_module(MOD)
class BenchmarkTests(unittest.TestCase):
 def test_parse_sizes(self):self.assertEqual(MOD.parse_sizes(['768x768','1024x1024']),[(768,768),(1024,1024)])
 def test_size_alignment(self):
  with self.assertRaises(ValueError):MOD.parse_sizes(['777x768'])
