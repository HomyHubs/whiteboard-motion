"""Contract tests: kwargs passed to VoxCPM must match the real voxcpm 2.x signature (no **kwargs catch-all)."""
import inspect,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from backend.providers.voice import VoxCPM2Provider,VoiceRequest

class StrictFakeVoxCPM:
    """Mirrors voxcpm 2.0.3 VoxCPM._generate keyword set; unknown kwargs raise TypeError like the real one."""
    def __init__(self):self.calls=[]
    def _generate(self,text,prompt_wav_path=None,prompt_text=None,reference_wav_path=None,cfg_value=2.0,inference_timesteps=10,
                  min_len=2,max_len=4096,normalize=False,denoise=False,retry_badcase=True,retry_badcase_max_times=3,
                  retry_badcase_ratio_threshold=6.0,streaming=False):
        if (prompt_wav_path is None)!=(prompt_text is None):raise ValueError('prompt_wav_path and prompt_text must both be provided or both be None')
        self.calls.append(dict(text=text,prompt_wav_path=prompt_wav_path,prompt_text=prompt_text,reference_wav_path=reference_wav_path))
        yield np.zeros(480,dtype=np.float32)
    def generate(self,*args,**kwargs):return next(self._generate(*args,streaming=False,**kwargs))
    def generate_streaming(self,*args,**kwargs):return self._generate(*args,streaming=True,**kwargs)

class FakeSoundFile:
    def __init__(self,path,**kwargs):self.path=Path(path)
    def __enter__(self):return self
    def write(self,array):pass
    def __exit__(self,*args):self.path.write_bytes(b'WAV')
FAKE_SF=types.SimpleNamespace(SoundFile=FakeSoundFile,write=lambda path,audio,sr:Path(path).write_bytes(b'WAV'))

class VoxCPMContractTests(unittest.TestCase):
    def provider(self):
        p=VoxCPM2Provider(Path('fake'));p._model=StrictFakeVoxCPM();return p
    def test_tts_kwargs_have_no_seed(self):
        kwargs=self.provider()._kwargs(VoiceRequest('xin chao',Path('a.wav'),seed=7))
        self.assertEqual(kwargs,{'text':'xin chao'})
    def test_clone_uses_reference_wav_path(self):
        kwargs=self.provider()._kwargs(VoiceRequest('hi',Path('a.wav'),reference_audio=Path('ref.wav'),consent_confirmed=True))
        self.assertEqual(kwargs,{'text':'hi','reference_wav_path':'ref.wav'})
    def test_clone_with_transcript_adds_prompt_pair(self):
        kwargs=self.provider()._kwargs(VoiceRequest('hi',Path('a.wav'),reference_audio=Path('ref.wav'),reference_text='mau',consent_confirmed=True))
        self.assertEqual((kwargs['prompt_wav_path'],kwargs['prompt_text'],kwargs['reference_wav_path']),('ref.wav','mau','ref.wav'))
    def test_streaming_and_non_streaming_accept_kwargs(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(sys.modules,{'soundfile':FAKE_SF}):
            p=self.provider()
            p.synthesize_streaming(VoiceRequest('hello',Path(tmp)/'s.wav'))
            p.synthesize(VoiceRequest('hello',Path(tmp)/'n.wav'))
            self.assertEqual(len(p._model.calls),2)
    def test_kwargs_match_installed_voxcpm(self):
        try:from voxcpm import VoxCPM
        except Exception:self.skipTest('voxcpm not installed')
        params=inspect.signature(VoxCPM._generate).parameters
        if any(p.kind is p.VAR_KEYWORD for p in params.values()):self.skipTest('installed voxcpm accepts **kwargs')
        kwargs=self.provider()._kwargs(VoiceRequest('hi',Path('a.wav'),reference_audio=Path('ref.wav'),reference_text='mau',consent_confirmed=True))
        self.assertEqual(set(kwargs)-set(params),set())

if __name__=='__main__':unittest.main()
