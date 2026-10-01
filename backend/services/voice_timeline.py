from __future__ import annotations
import hashlib,threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from ..providers.voice import VoiceRequest,VoxCPM2Provider,VoiceProgress

@dataclass(frozen=True)
class TimelineProgress:
    cue_index:int;cue_count:int;cue_progress:VoiceProgress|None;message:str

def cue_filename(cue:dict)->str:
    digest=hashlib.sha256(f"{cue['index']}|{cue['text']}".encode()).hexdigest()[:12]
    return f"cue-{int(cue['index']):03d}-{digest}.wav"

def generate_timeline_clips(cues:list[dict],provider:VoxCPM2Provider,workdir:Path,language:str='vi',reference_audio:Path|None=None,reference_text:str='',consent_confirmed:bool=False,cancel_event:threading.Event|None=None,on_progress:Callable[[TimelineProgress],None]|None=None)->list[Path]:
    workdir.mkdir(parents=True,exist_ok=True);clips=[];total=len(cues)
    for position,cue in enumerate(cues,1):
        if cancel_event and cancel_event.is_set():raise RuntimeError('Timeline generation cancelled')
        output=workdir/cue_filename(cue)
        def progress(value:VoiceProgress,index=position):
            if on_progress:on_progress(TimelineProgress(index,total,value,f"Cue {index}/{total}"))
        request=VoiceRequest(cue['text'],output,language,reference_audio,reference_text,consent_confirmed,int(cue.get('index',position)))
        provider.synthesize_streaming(request,cancel_event=cancel_event,on_progress=progress);clips.append(output)
        if on_progress:on_progress(TimelineProgress(position,total,None,f"Completed cue {position}/{total}"))
    return clips
