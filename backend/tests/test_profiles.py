import unittest
from backend.hardware import NvidiaGpu, gpu_series
from backend.profiles import select_qwen_profile

class ProfileTests(unittest.TestCase):
    def gpu(self, name, mb): return NvidiaGpu(0, name, mb, "999.0", "12.0")
    def test_series(self):
        self.assertEqual(gpu_series("NVIDIA GeForce RTX 5060 Ti"), 50)
    def test_4060(self):
        self.assertEqual(select_qwen_profile(self.gpu("NVIDIA GeForce RTX 4060", 8188)).id, "rtx-4060-8gb")
    def test_5060(self):
        p = select_qwen_profile(self.gpu("NVIDIA GeForce RTX 5060", 8188))
        self.assertEqual((p.id, p.runtime), ("rtx-5060-8gb", "cuda-blackwell"))
    def test_5060ti(self):
        self.assertEqual(select_qwen_profile(self.gpu("NVIDIA GeForce RTX 5060 Ti", 16384)).id, "rtx-5060ti-16gb")
    def test_3060(self):
        self.assertEqual(select_qwen_profile(self.gpu("NVIDIA GeForce RTX 3060", 12288)).id, "rtx-3060-12gb")
