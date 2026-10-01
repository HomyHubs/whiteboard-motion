import tempfile,unittest
from pathlib import Path
from backend.cache import AudioCache,AudioCacheKey
class AudioCacheTests(unittest.TestCase):
 def key(self,text='hello'):return AudioCacheKey('voxcpm2','rev1',text,'vi',42,settings={'speed':1})
 def test_store_restore(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source.wav';source.write_bytes(b'audio');cache=AudioCache(root/'cache');cache.store(self.key(),source,{'samples':10});out=root/'out.wav';metadata=cache.restore(self.key(),out)
   self.assertEqual(out.read_bytes(),b'audio');self.assertEqual(metadata['samples'],10)
 def test_key_invalidates(self):self.assertNotEqual(self.key('a').digest(),self.key('b').digest())
 def test_corruption_is_miss(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'s.wav';source.write_bytes(b'a');cache=AudioCache(root/'c');audio,_=cache.paths(self.key());cache.store(self.key(),source);audio.write_bytes(b'bad');self.assertIsNone(cache.restore(self.key(),root/'out.wav'))
