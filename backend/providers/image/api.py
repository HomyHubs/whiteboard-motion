from __future__ import annotations
import base64,json,math,os,time,urllib.request,uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .base import ImageRequest
from ...security.credentials import CredentialStore,WindowsCredentialStore

@dataclass(frozen=True)
class ApiProviderConfig:
    id:str;kind:str;endpoint:str;model:str='';credential_target:str='';api_key_env:str=''

def _write(output:Path,payload:bytes)->Path:
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(payload);return output

def _download(url:str)->bytes:
    with urllib.request.urlopen(url,timeout=300) as response:return response.read()

def _extract_image(data:dict[str,Any])->bytes:
    items=data.get('data') or data.get('images') or []
    if not items:raise RuntimeError('API response contains no image data')
    item=items[0] if isinstance(items,list) else items
    if isinstance(item,str):return _download(item) if item.startswith('http') else base64.b64decode(item)
    encoded=item.get('b64_json') or item.get('base64') or item.get('image')
    if encoded:return base64.b64decode(encoded)
    if item.get('url'):return _download(item['url'])
    raise RuntimeError('API image mapping did not find base64 or URL')

class ImageApiProvider:
    def __init__(self,config:ApiProviderConfig,credential_store:CredentialStore|None=None):
        self.config=config;self.credential_store=credential_store
    def _key(self)->str:
        key=None
        if self.config.credential_target:
            store=self.credential_store
            if store is None:store=WindowsCredentialStore()
            key=store.get(self.config.credential_target)
        if not key and self.config.api_key_env:key=os.environ.get(self.config.api_key_env)
        if not key:raise RuntimeError(f'Missing credential: {self.config.credential_target or self.config.api_key_env}')
        return key

class OpenAICompatibleImageProvider(ImageApiProvider):
    def generate(self,request:ImageRequest)->Path:
        body={'model':self.config.model,'prompt':request.prompt,'size':f'{request.width}x{request.height}','n':1,'response_format':'b64_json'}
        req=urllib.request.Request(self.config.endpoint,data=json.dumps(body).encode(),headers={'Authorization':f'Bearer {self._key()}','Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=300) as response:data=json.load(response)
        return _write(request.output,_extract_image(data))

class StabilityImageProvider(ImageApiProvider):
    @staticmethod
    def _multipart(fields:dict[str,str])->tuple[bytes,str]:
        boundary='----Whiteboard'+uuid.uuid4().hex;chunks=[]
        for name,value in fields.items():chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()]
        chunks.append(f'--{boundary}--\r\n'.encode());return b''.join(chunks),boundary
    def generate(self,request:ImageRequest)->Path:
        divisor=math.gcd(request.width,request.height);ratio=f'{request.width//divisor}:{request.height//divisor}';body,boundary=self._multipart({'prompt':request.prompt,'negative_prompt':request.negative_prompt,'aspect_ratio':ratio,'output_format':'png'})
        req=urllib.request.Request(self.config.endpoint,data=body,headers={'Authorization':f'Bearer {self._key()}','Accept':'image/*','Content-Type':f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req,timeout=300) as response:
            payload=response.read();ctype=response.headers.get('Content-Type','')
        if 'json' in ctype:payload=_extract_image(json.loads(payload))
        return _write(request.output,payload)

class ReplicateImageProvider(ImageApiProvider):
    def generate(self,request:ImageRequest)->Path:
        headers={'Authorization':f'Bearer {self._key()}','Content-Type':'application/json','Prefer':'wait=60'}
        body={'input':{'prompt':request.prompt,'width':request.width,'height':request.height,'num_inference_steps':request.steps,'seed':request.seed}}
        req=urllib.request.Request(self.config.endpoint,data=json.dumps(body).encode(),headers=headers)
        with urllib.request.urlopen(req,timeout=120) as response:data=json.load(response)
        poll=(data.get('urls') or {}).get('get')
        while data.get('status') not in {'succeeded','failed','canceled'}:
            if not poll:raise RuntimeError('Replicate response has no polling URL')
            time.sleep(1);poll_req=urllib.request.Request(poll,headers={'Authorization':headers['Authorization']})
            with urllib.request.urlopen(poll_req,timeout=60) as response:data=json.load(response)
        if data.get('status')!='succeeded':raise RuntimeError(f"Replicate {data.get('status')}: {data.get('error')}")
        output=data.get('output');url=output[0] if isinstance(output,list) else output
        if not isinstance(url,str):raise RuntimeError('Replicate output mapping did not return an URL')
        return _write(request.output,_download(url))

def create_api_provider(config:ApiProviderConfig,credential_store:CredentialStore|None=None)->ImageApiProvider:
    kind=config.kind.lower()
    if kind in {'openai','openai-compatible','together'}:return OpenAICompatibleImageProvider(config,credential_store)
    if kind=='stability':return StabilityImageProvider(config,credential_store)
    if kind=='replicate':return ReplicateImageProvider(config,credential_store)
    raise ValueError(f'Unsupported image API provider kind: {config.kind}')

# Backward-compatible name.
class ApiImageProvider(OpenAICompatibleImageProvider):
    def __init__(self,endpoint:str,model:str,api_key_env:str='IMAGE_API_KEY'):
        super().__init__(ApiProviderConfig('legacy','openai-compatible',endpoint,model,api_key_env=api_key_env))
