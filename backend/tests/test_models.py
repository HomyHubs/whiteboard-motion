import tempfile, unittest
from pathlib import Path
from backend.models import ModelManager

class ModelManagerTests(unittest.TestCase):
    def test_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ModelManager(Path(tmp))
            rows = manager.list_status()
            self.assertGreaterEqual(len(rows), 2)
            self.assertFalse(any(row["installed"] for row in rows))
