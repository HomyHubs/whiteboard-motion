import os,tempfile,unittest
from pathlib import Path
from unittest import mock
from backend.providers.image.qwen_local import OFFLOAD_ENV,choose_offload,component_bytes
GB=1024**3

class QwenOffloadTests(unittest.TestCase):
    def setUp(self):
        self.env=mock.patch.dict(os.environ,{},clear=False);self.env.start();os.environ.pop(OFFLOAD_ENV,None)
    def tearDown(self):self.env.stop()
    def test_5060ti_bf16_transformer_does_not_fit_uses_sequential(self):
        # Measured 2026-10-02: transformer 13.3 GB, ~12 GB free -> model offload crashed with 0xC0000005.
        self.assertEqual(choose_offload(True,int(13.3*GB),12*GB),'sequential')
    def test_fits_uses_model_offload(self):
        self.assertEqual(choose_offload(True,8*GB,15*GB),'model')
    def test_unknown_free_vram_keeps_model_offload(self):
        self.assertEqual(choose_offload(True,int(13.3*GB),None),'model')
    def test_no_cpu_offload_profile(self):
        self.assertEqual(choose_offload(False,int(13.3*GB),12*GB),'none')
    def test_env_override_and_validation(self):
        with mock.patch.dict(os.environ,{OFFLOAD_ENV:'model'}):
            self.assertEqual(choose_offload(True,int(13.3*GB),12*GB),'model')
        with self.assertRaises(ValueError):choose_offload(True,1,1,requested='gpu')
    def test_component_bytes_sums_safetensors(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'transformer';folder.mkdir()
            (folder/'a.safetensors').write_bytes(b'x'*10);(folder/'b.safetensors').write_bytes(b'x'*5);(folder/'index.json').write_bytes(b'{}')
            self.assertEqual(component_bytes(Path(tmp)),15)
            self.assertEqual(component_bytes(Path(tmp),'missing'),0)

if __name__=='__main__':unittest.main()
