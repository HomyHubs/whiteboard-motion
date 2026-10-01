from __future__ import annotations
import base64,json,math,os,threading,time,urllib.request,uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any,Callable
from .base import ImageRequest
from ...security.credentials import CredentialStore,WindowsCredentialStore
from ...net import HttpClient,RequestCancelled

@dataclass(frozen=True)
class ApiProviderConfig:
    id:str;kind:str;endpoint:str;model:str='';credential_target:str='';api_key_env:str=''
    estimated_cost_per_image_usd:float|None=None;max_cost_per_job_usd:float|None=None
@dataclass(frozen=True)
class ApiProgress:
    stage:str;progress:float|None;message:str
ProgressCallback=Callable[[ApiProgress],None]
class CostLimitExceeded(RuntimeError):pass

def _write(output:Path,payload:bytes)->Path:output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(payload);return output

def _extract_image(data:dict[str,Any],download:Callable[[str],bytes])->bytes:
    items=data.get('data') or data.get('images') or []
    if not items:raise RuntimeError('API response contains no image data')
    item=items[0] if isinstance(items,list) else items
    if isinstance(item,str):return download(item) if item.startswith('http') else base64.b64decode(item)
    encoded=item.get('b64_json') or item.get('base64') or item.get('image')
    if encoded:return base64.b64decode(encoded)
    if item.get('url'):return download(item['url'])
    raise RuntimeError('API image mapping did not find base64 or URL')

class ImageApiProvider:
    def __init__(self,config:ApiProviderConfig,credential_store:CredentialStore|None=None,http:HttpClient|None=None,cancel_event:threading.Event|None=None,on_progress:ProgressCallback|None=None):
        self.config=config;self.credential_store=credential_store;self.http=http or HttpClient();self.cancel_event=cancel_event;self.on_progress=on_progress
    def _emit(self,stage:str,progress:float|None,message:str):
        if self.on_progress:self.on_progress(ApiProgress(stage,progress,message))
    def _http_progress(self,stage,progress,message):self._emit(stage,progress,message)
    def _key(self)->str:
        key=None
        if self.config.credential_target:
            store=self.credential_store or WindowsCredentialStore();key=store.get(self.config.credential_target)
        if not key and self.config.api_key_env:key=os.environ.get(self.config.api_key_env)
        if not key:raise RuntimeError(f'Missing credential: {self.config.credential_target or self.config.api_key_env}')
        return key
    def _budget(self,count:int=1)->float|None:
        price=self.config.estimated_cost_per_image_usd;estimated=price*count if price is not None else None;limit=self.config.max_cost_per_job_usd
        if estimated is not None and limit is not None and estimated>limit:raise CostLimitExceeded(f'Estimated cost ${estimated:.4f} exceeds job budget ${limit:.4f}')
        self._emit('cost',0.0,f'Estimated cost: {"unknown" if estimated is None else f"${estimated:.4f}"}')
        return estimated
    def _download(self,url:str)->bytes:
        req=urllib.request.Request(url,headers={'User-Agent':'whiteboard-video/0.3'});return self.http.request(req,cancel_event=self.cancel_event,progress=self._http_progress).body
    def _json(self,request:urllib.request.Request,timeout=300)->dict:
        return self.http.request(request,timeout,cancel_event=self.cancel_event,progress=self._http_progress).json()
    def _wait(self,seconds:float):
        if self.cancel_event:
            if self.cancel_event.wait(seconds):raise RequestCancelled('Request cancelled while polling')
        else:time.sleep(seconds)

class OpenAICompatibleImageProvider(ImageApiProvider):
    def generate(self,request:ImageRequest)->Path:
        self._budget();body={'model':self.config.model,'prompt':request.prompt,'size':f'{request.width}x{request.height}','n':1,'response_format':'b64_json'}
        req=urllib.request.Request(self.config.endpoint,data=json.dumps(body).encode(),headers={'Authorization':f'Bearer {self._key()}','Content-Type':'application/json'})
        data=self._json(req);payload=_extract_image(data,self._download);self._emit('write',1.0,str(request.output));return _write(request.output,payload)

class StabilityImageProvider(ImageApiProvider):
    @staticmethod
    def _multipart(fields:dict[str,str])->tuple[bytes,str]:
        boundary='----Whiteboard'+uuid.uuid4().hex;chunks=[]
        for name,value in fields.items():chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()]
        chunks.append(f'--{boundary}--\r\n'.encode());return b''.join(chunks),boundary
    def generate(self,request:ImageRequest)->Path:
        self._budget();divisor=math.gcd(request.width,request.height);ratio=f'{request.width//divisor}:{request.height//divisor}';body,boundary=self._multipart({'prompt':request.prompt,'negative_prompt':request.negative_prompt,'aspect_ratio':ratio,'output_format':'png'})
        req=urllib.request.Request(self.config.endpoint,data=body,headers={'Authorization':f'Bearer {self._key()}','Accept':'image/*','Content-Type':f'multipart/form-data; boundary={boundary}'})
        response=self.http.request(req,cancel_event=self.cancel_event,progress=self._http_progress);payload=response.body
        if 'json' in response.headers.get('Content-Type',''):payload=_extract_image(json.loads(payload),self._download)
        self._emit('write',1.0,str(request.output));return _write(request.output,payload)

class ReplicateImageProvider(ImageApiProvider):
    def generate(self,request:ImageRequest)->Path:
        self._budget();headers={'Authorization':f'Bearer {self._key()}','Content-Type':'application/json','Prefer':'wait=60'};body={'input':{'prompt':request.prompt,'width':request.width,'height':request.height,'num_inference_steps':request.steps,'seed':request.seed}}
        data=self._json(urllib.request.Request(self.config.endpoint,data=json.dumps(body).encode(),headers=headers),120);poll=(data.get('urls') or {}).get('get');poll_count=0
        while data.get('status') not in {'succeeded','failed','canceled'}:
            if not poll:raise RuntimeError('Replicate response has no polling URL')
            self._wait(1);poll_count+=1;self._emit('poll',None,f'Poll {poll_count}: {data.get("status")}');data=self._json(urllib.request.Request(poll,headers={'Authorization':headers['Authorization']}),60)
        if data.get('status')!='succeeded':raise RuntimeError(f"Replicate {data.get('status')}: {data.get('error')}")
        output=data.get('output');url=output[0] if isinstance(output,list) else output
        if not isinstance(url,str):raise RuntimeError('Replicate output mapping did not return an URL')
        payload=self._download(url);self._emit('write',1.0,str(request.output));return _write(request.output,payload)

def create_api_provider(config:ApiProviderConfig,credential_store:CredentialStore|None=None,**kwargs)->ImageApiProvider:
    kind=config.kind.lower()
    cls=OpenAICompatibleImageProvider if kind in {'openai','openai-compatible','together'} else StabilityImageProvider if kind=='stability' else ReplicateImageProvider if kind=='replicate' else None
    if cls is None:raise ValueError(f'Unsupported image API provider kind: {config.kind}')
    return cls(config,credential_store,**kwargs)
class ApiImageProvider(OpenAICompatibleImageProvider):
    def __init__(self,endpoint:str,model:str,api_key_env:str='IMAGE_API_KEY'):
        super().__init__(ApiProviderConfig('legacy','openai-compatible',endpoint,model,api_key_env=api_key_env))
