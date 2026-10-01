import tempfile,unittest
from pathlib import Path
from backend.services.voice_timeline import cue_filename,generate_timeline_clips
from backend.providers.voice import VoiceProgress
class FakeProvider:
 def __init__(self):self.requests=[]
 def synthesize_streaming(self,request,cancel_event=None,on_progress=None):
  self.requests.append(request);request.output.write_bytes(b'wav')
  if on_progress:on_progress(VoiceProgress(1,480,0.01,True,False))
class TimelineTests(unittest.TestCase):
 def test_filename_stable(self):
  cue={'index':1,'text':'hello'};self.assertEqual(cue_filename(cue),cue_filename(cue))
 def test_generate_order(self):
  with tempfile.TemporaryDirectory() as tmp:
   cues=[{'index':1,'text':'xin chao'},{'index':2,'text':'hello'}];provider=FakeProvider();events=[];clips=generate_timeline_clips(cues,provider,Path(tmp),on_progress=events.append)
   self.assertEqual([x.text for x in provider.requests],['xin chao','hello']);self.assertEqual(len(clips),2);self.assertTrue(all(x.exists() for x in clips));self.assertEqual(events[-1].cue_index,2)
