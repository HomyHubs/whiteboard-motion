import unittest
from backend.security.credentials import InMemoryCredentialStore,credential_target,WindowsCredentialStore
class CredentialTests(unittest.TestCase):
 def test_memory_roundtrip(self):
  store=InMemoryCredentialStore();target=credential_target('openai');store.set(target,'secret');self.assertEqual(store.get(target),'secret');self.assertTrue(store.delete(target));self.assertIsNone(store.get(target))
 def test_target_namespace(self):self.assertEqual(credential_target('x'),'WhiteboardVideo/image-api/x')
 def test_windows_store_rejected_off_windows(self):
  import os
  if os.name!='nt':
   with self.assertRaises(OSError):WindowsCredentialStore()
