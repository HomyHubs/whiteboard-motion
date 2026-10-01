import sys,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from backend.providers.voice import VoxCPM2Provider,VoiceRequest,VoiceGenerationCancelled
from backend.cache import AudioCache
class FakeModel:
 def generate_streaming(self,**kwargs):
  yield np.ones(480,dtype=np.float32)*.1
  yield np.ones(960,dtype=np.float32)*.2
class FakeSoundFile:
 total=0
 def __init__(self,path,**kwargs):self.path=Path(path);self.total=0
 def __enter__(self):self.path.write_bytes(b'');return self
 def write(self,array):self.total+=len(array);FakeSoundFile.total=self.total
 def __exit__(self,*args):self.path.write_bytes(b'WAV')
FAKE_SF=types.SimpleNamespace(SoundFile=FakeSoundFile)
class VoxStreamingTests(unittest.TestCase):
 def provider(self):p=VoxCPM2Provider(Path('fake'));p._model=FakeModel();return p
 def test_streaming_writes_wav_and_progress(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(sys.modules,{'soundfile':FAKE_SF}):
   out=Path(tmp)/'voice.wav';events=[];self.provider().synthesize_streaming(VoiceRequest('hello',out),on_progress=events.append)
   self.assertTrue(out.exists());self.assertEqual(FakeSoundFile.total,1440);self.assertTrue(events[-1].finished);self.assertEqual(events[-1].chunks,2)
 def test_cancel_removes_partial(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(sys.modules,{'soundfile':FAKE_SF}):
   out=Path(tmp)/'voice.wav';event=threading.Event()
   def progress(value):event.set()
   with self.assertRaises(VoiceGenerationCancelled):self.provider().synthesize_streaming(VoiceRequest('hello',out),cancel_event=event,on_progress=progress)
   self.assertFalse(out.exists());self.assertFalse((Path(tmp)/'voice.part.wav').exists())
 def test_streaming_cache_hit_skips_model(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict(sys.modules,{'soundfile':FAKE_SF}):
   root=Path(tmp);cache=AudioCache(root/'cache');first=self.provider();first.cache=cache;first.model_revision='rev';first.synthesize_streaming(VoiceRequest('hello',root/'a.wav'))
   second=VoxCPM2Provider(Path('fake'),cache=cache,model_revision='rev');events=[];second.synthesize_streaming(VoiceRequest('hello',root/'b.wav'),on_progress=events.append)
   self.assertIsNone(second._model);self.assertTrue(events[-1].cached);self.assertEqual((root/'b.wav').read_bytes(),(root/'a.wav').read_bytes())
 def test_stream_requires_wav(self):
  with self.assertRaises(ValueError):self.provider().synthesize_streaming(VoiceRequest('hello',Path('voice.mp3')))
