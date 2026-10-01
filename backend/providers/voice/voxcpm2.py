from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Callable

@dataclass
class VoiceRequest:
    text:str;output:Path;language:str='vi';reference_audio:Path|None=None;reference_text:str|None=None;consent_confirmed:bool=False;seed:int=42
@dataclass(frozen=True)
class VoiceProgress:
    chunks:int;samples:int;seconds:float;finished:bool=False
class VoiceGenerationCancelled(RuntimeError):pass

class VoxCPM2Provider:
    SAMPLE_RATE=48000
    def __init__(self,model_path:Path,device:str='cuda',optimize:bool=True):self.model_path,self.device,self.optimize=model_path,device,optimize;self._model=None
    def load(self)->None:
        if self._model is not None:return
        try:from voxcpm import VoxCPM
        except ImportError as exc:raise RuntimeError('Thiếu package voxcpm') from exc
        self._model=VoxCPM.from_pretrained(hf_model_id=str(self.model_path),device=self.device,optimize=self.optimize,load_denoiser=False)
    def _kwargs(self,request:VoiceRequest)->dict:
        if request.reference_audio and not request.consent_confirmed:raise PermissionError('Voice clone yêu cầu xác nhận quyền sử dụng giọng mẫu')
        kwargs={'text':request.text,'seed':request.seed}
        if request.reference_audio:kwargs.update(prompt_wav_path=str(request.reference_audio),prompt_text=request.reference_text or '')
        return kwargs
    def synthesize(self,request:VoiceRequest)->Path:
        self.load();audio=self._model.generate(**self._kwargs(request))
        try:import soundfile as sf
        except ImportError as exc:raise RuntimeError('Thiếu soundfile') from exc
        request.output.parent.mkdir(parents=True,exist_ok=True);sf.write(str(request.output),audio,self.SAMPLE_RATE);return request.output
    def synthesize_streaming(self,request:VoiceRequest,cancel_event:threading.Event|None=None,on_progress:Callable[[VoiceProgress],None]|None=None,check_cancelled:Callable[[],None]|None=None)->Path:
        if request.output.suffix.lower() not in {'.wav','.wave'}:raise ValueError('Streaming output must be WAV')
        self.load();kwargs=self._kwargs(request)
        try:import numpy as np;import soundfile as sf
        except ImportError as exc:raise RuntimeError('Streaming requires numpy and soundfile') from exc
        def check():
            if cancel_event and cancel_event.is_set():raise VoiceGenerationCancelled('Voice generation cancelled')
            if check_cancelled:check_cancelled()
        part=request.output.with_name(request.output.stem+'.part.wav');request.output.parent.mkdir(parents=True,exist_ok=True);part.unlink(missing_ok=True);chunks=samples=0
        try:
            with sf.SoundFile(str(part),mode='w',samplerate=self.SAMPLE_RATE,channels=1,subtype='PCM_16') as writer:
                for chunk in self._model.generate_streaming(**kwargs):
                    check()
                    if hasattr(chunk,'detach'):chunk=chunk.detach().float().cpu().numpy()
                    array=np.asarray(chunk,dtype=np.float32).reshape(-1)
                    if not array.size:continue
                    writer.write(array);chunks+=1;samples+=int(array.size)
                    if on_progress:on_progress(VoiceProgress(chunks,samples,samples/self.SAMPLE_RATE,False))
                check()
            part.replace(request.output)
            if on_progress:on_progress(VoiceProgress(chunks,samples,samples/self.SAMPLE_RATE,True))
            return request.output
        except BaseException:
            part.unlink(missing_ok=True);request.output.unlink(missing_ok=True);raise
    def unload(self)->None:
        self._model=None
        try:
            import torch
            if torch.cuda.is_available():torch.cuda.empty_cache()
        except ImportError:pass
