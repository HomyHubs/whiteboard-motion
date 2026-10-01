from __future__ import annotations
from dataclasses import asdict,dataclass
import hashlib,json,os,shutil
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class AudioCacheKey:
    engine:str;model_revision:str;text:str;language:str;seed:int;reference_sha256:str='';reference_text:str='';settings:dict[str,Any]|None=None;format:str='wav'
    def digest(self)->str:
        payload=json.dumps(asdict(self),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();return hashlib.sha256(payload).hexdigest()

def file_sha256(path:Path|None)->str:
    if path is None:return ''
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

class AudioCache:
    def __init__(self,root:Path):self.root=root;self.root.mkdir(parents=True,exist_ok=True)
    def paths(self,key:AudioCacheKey)->tuple[Path,Path]:
        digest=key.digest();folder=self.root/digest[:2]/digest[2:4];return folder/f'{digest}.audio',folder/f'{digest}.json'
    def restore(self,key:AudioCacheKey,output:Path)->dict|None:
        audio,metadata=self.paths(key)
        if not audio.is_file() or not metadata.is_file():return None
        try:data=json.loads(metadata.read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError):return None
        if data.get('key')!=asdict(key) or data.get('audio_sha256')!=file_sha256(audio):return None
        output.parent.mkdir(parents=True,exist_ok=True);tmp=output.with_name(output.name+'.cache.part');shutil.copy2(audio,tmp);os.replace(tmp,output);return data
    def store(self,key:AudioCacheKey,source:Path,extra:dict|None=None)->Path:
        audio,metadata=self.paths(key);audio.parent.mkdir(parents=True,exist_ok=True);audio_tmp=audio.with_suffix('.audio.part');meta_tmp=metadata.with_suffix('.json.part');shutil.copy2(source,audio_tmp);digest=file_sha256(audio_tmp)
        data={'schemaVersion':1,'key':asdict(key),'audio_sha256':digest,'bytes':audio_tmp.stat().st_size,**(extra or {})};meta_tmp.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2),encoding='utf-8');os.replace(audio_tmp,audio);os.replace(meta_tmp,metadata);return audio
    def remove(self,key:AudioCacheKey)->None:
        for path in self.paths(key):path.unlink(missing_ok=True)
