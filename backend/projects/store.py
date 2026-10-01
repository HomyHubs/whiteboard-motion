from __future__ import annotations
from datetime import datetime,timezone
import json,os,re,uuid
from pathlib import Path
from typing import Any
from ..config import app_data_dir

ID_RE=re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')
class InvalidProjectId(ValueError):pass
def now():return datetime.now(timezone.utc).isoformat()
def slugify(value:str)->str:
    value=re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')[:50]
    return value or 'project'
class ProjectStore:
    def __init__(self,root:Path|None=None):self.root=root or app_data_dir()/'projects';self.root.mkdir(parents=True,exist_ok=True)
    def _id(self,value:str)->str:
        if not ID_RE.fullmatch(value):raise InvalidProjectId(value)
        return value
    def path(self,project_id:str)->Path:return self.root/self._id(project_id)
    def _write(self,path:Path,data:dict)->None:
        path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,path)
    def create(self,name:str,aspect_ratio:str='16:9')->dict:
        base=slugify(name);project_id=base
        while self.path(project_id).exists():project_id=f'{base[:54]}-{uuid.uuid4().hex[:6]}'
        data={'id':project_id,'name':name.strip() or project_id,'aspectRatio':aspect_ratio,'createdAt':now(),'updatedAt':now()};self._write(self.path(project_id)/'project.json',data);(self.path(project_id)/'scenes').mkdir(exist_ok=True);return data
    def get(self,project_id:str)->dict:
        path=self.path(project_id)/'project.json'
        if not path.is_file():raise KeyError(project_id)
        data=json.loads(path.read_text(encoding='utf-8'));data['scenes']=self.list_scenes(project_id);return data
    def list(self)->list[dict]:
        output=[]
        for path in self.root.glob('*/project.json'):
            try:output.append(json.loads(path.read_text(encoding='utf-8')))
            except (OSError,json.JSONDecodeError):continue
        return sorted(output,key=lambda x:x.get('updatedAt',''),reverse=True)
    def list_scenes(self,project_id:str)->list[str]:return sorted(p.stem.replace('.manifest','') for p in (self.path(project_id)/'scenes').glob('*.manifest.json'))
    def load_scene(self,project_id:str,scene_id:str)->dict:
        path=self.path(project_id)/'scenes'/f'{self._id(scene_id)}.manifest.json'
        if not path.is_file():raise KeyError(scene_id)
        return json.loads(path.read_text(encoding='utf-8'))
    def save_scene(self,project_id:str,scene_id:str,data:dict[str,Any])->dict:
        self.get(project_id);scene_id=self._id(scene_id)
        if not isinstance(data,dict):raise ValueError('Scene manifest must be an object')
        data={**data,'sceneId':data.get('sceneId') or scene_id};self._write(self.path(project_id)/'scenes'/f'{scene_id}.manifest.json',data)
        project=json.loads((self.path(project_id)/'project.json').read_text(encoding='utf-8'));project['updatedAt']=now();self._write(self.path(project_id)/'project.json',project);return data
