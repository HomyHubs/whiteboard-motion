#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.models import ModelManager
from backend.providers.prompt import PromptEnhancer

def main():
 p=argparse.ArgumentParser();p.add_argument('prompt');p.add_argument('--task',choices=['t2i','edit'],default='t2i');p.add_argument('--image',action='append',default=[]);p.add_argument('--dtype',choices=['bfloat16','float16','float32'],default='bfloat16')
 a=p.parse_args();model_id='qwen-image-2.1-pe-t2i' if a.task=='t2i' else 'qwen-image-2.1-pe-i2i';m=ModelManager()
 if not m.is_installed(model_id):raise SystemExit(f'Missing {model_id}; accept license and download it first')
 result=PromptEnhancer(m.path(model_id),a.task,dtype=a.dtype).enhance(a.prompt,[Path(x) for x in a.image]);print(json.dumps(result.__dict__,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
