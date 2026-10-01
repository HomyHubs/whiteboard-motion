import unittest
from unittest import mock
from backend import hardware
from backend.profiles import select_qwen_profile

class NoGpuTests(unittest.TestCase):
    """P4.6: behaviour on machines without NVIDIA (nvidia-smi missing or failing)."""
    def test_nvidia_smi_missing(self):
        with mock.patch.object(hardware.shutil, "which", return_value=None):
            self.assertEqual(hardware.hardware_report(), {"nvidia": [], "hasNvidia": False})
    def test_nvidia_smi_fails(self):
        failed = mock.Mock(returncode=9, stdout="", stderr="NVIDIA-SMI has failed")
        with mock.patch.object(hardware.shutil, "which", return_value="nvidia-smi"), \
             mock.patch.object(hardware.subprocess, "run", return_value=failed):
            self.assertEqual(hardware.detect_nvidia_gpus(), [])
    def test_cpu_profile(self):
        p = select_qwen_profile(None)
        self.assertEqual((p.id, p.runtime), ("cpu-experimental", "cpu"))
