#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, platform, shutil, subprocess, sys, threading, time
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
if hasattr(sys.stderr, "reconfigure"):
    try: sys.stderr.reconfigure(encoding="utf-8")
    except Exception: pass
from backend.hardware import detect_nvidia_gpus
from backend.models import ModelManager
from backend.profiles import select_qwen_profile
from backend.providers.image.base import ImageRequest
from backend.providers.image.factory import create_qwen_provider

@dataclass
class GpuSample:
    timestamp_s: float
    memory_used_mb: int
    utilization_percent: int
    temperature_c: int

def query_gpu(index:int)->GpuSample|None:
    exe=shutil.which('nvidia-smi')
    if not exe:return None
    cmd=[exe,f'--id={index}','--query-gpu=memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']
    result=subprocess.run(cmd,capture_output=True,text=True,check=False)
    if result.returncode:return None
    try:
        values=[int(float(v.strip())) for v in result.stdout.strip().split(',')]
        return GpuSample(time.time(),values[0],values[1],values[2])
    except (ValueError,IndexError):return None

class Monitor:
    def __init__(self,index:int,interval:float=.25):self.index=index;self.interval=interval;self.samples=[];self.stop=threading.Event()
    def run(self):
        while not self.stop.is_set():
            sample=query_gpu(self.index)
            if sample:self.samples.append(sample)
            self.stop.wait(self.interval)

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def system_ram_mb()->int|None:
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
        status=MEMORYSTATUSEX();status.dwLength=ctypes.sizeof(status);ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status));return status.ullTotalPhys//(1024*1024)
    except Exception:return None

def parse_sizes(values:list[str])->list[tuple[int,int]]:
    output=[]
    for value in values:
        parts=value.lower().split('x')
        if len(parts)!=2:raise ValueError(f'Invalid size: {value}')
        w,h=map(int,parts)
        if w%16 or h%16:raise ValueError('Sizes must be multiples of 16')
        output.append((w,h))
    return output

def with_backend(profile,backend:str):
    if backend=='auto':return profile
    return replace(profile,backend=backend,notes=profile.notes+f' Backend override: {backend}.')

def preflight(profile,manager:ModelManager)->dict:
    ids=['qwen-image-2.1'] if profile.backend=='diffusers' else ['qwen-image-2.1-ncnn','qwenimage-ncnn-windows-runtime']
    return {'backend':profile.backend,'requiredModels':[{'id':x,'installed':manager.is_installed(x),'licenseAccepted':manager.is_license_accepted(x)} for x in ids]}

def main(argv=None)->int:
    p=argparse.ArgumentParser(description='Benchmark Qwen-Image-2.1 local backend on Windows/NVIDIA')
    p.add_argument('--sizes',nargs='+',default=['768x768','1024x1024'])
    p.add_argument('--steps',type=int,default=20)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--gpu',type=int,default=0)
    p.add_argument('--expected-gpu',help='Required case-insensitive text in GPU name, e.g. RTX 4060')
    p.add_argument('--backend',choices=['auto','ncnn-vulkan','diffusers'],default='auto')
    p.add_argument('--preflight-only',action='store_true')
    p.add_argument('--prompt',default='Simple whiteboard drawing of a red umbrella beside a stack of books, clean dark pencil outlines, cream paper, no text, no logo')
    p.add_argument('--output-dir',type=Path,default=ROOT/'benchmarks'/'outputs')
    p.add_argument('--report',type=Path)
    args=p.parse_args(argv)
    gpus=detect_nvidia_gpus()
    if args.gpu>=len(gpus):raise SystemExit(f'GPU index {args.gpu} unavailable; detected {len(gpus)}')
    gpu=gpus[args.gpu]
    if args.expected_gpu and args.expected_gpu.lower() not in gpu.name.lower():raise SystemExit(f'Expected {args.expected_gpu}, got {gpu.name}')
    profile=with_backend(select_qwen_profile(gpu),args.backend);manager=ModelManager();check=preflight(profile,manager)
    if args.preflight_only:
        print(json.dumps({'gpu':gpu.to_dict(),'profile':profile.to_dict(),'preflight':check},ensure_ascii=False,indent=2));return 0 if all(x['installed'] and x['licenseAccepted'] for x in check['requiredModels']) else 3
    missing=[x['id'] for x in check['requiredModels'] if not x['installed']]
    if missing:raise SystemExit('Missing models: '+', '.join(missing))
    provider=create_qwen_provider(profile,manager,args.gpu)
    sizes=parse_sizes(args.sizes);args.output_dir.mkdir(parents=True,exist_ok=True)
    report={
      'schemaVersion':1,'createdAt':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
      'python':sys.version,'systemRamMb':system_ram_mb(),'gpu':gpu.to_dict(),'profile':profile.to_dict(),
      'modelRevisions':{m['id']:m['revision'] for m in manager.entries()},'settings':{'steps':args.steps,'seed':args.seed,'prompt':args.prompt},'runs':[]}
    for width,height in sizes:
        output=args.output_dir/f'{profile.id}-{width}x{height}-s{args.steps}.png';monitor=Monitor(args.gpu);thread=threading.Thread(target=monitor.run,daemon=True);thread.start();started=time.perf_counter()
        run={'width':width,'height':height,'status':'failed'}
        try:
            provider.generate(ImageRequest(args.prompt,output,width,height,args.steps,args.seed));elapsed=time.perf_counter()-started
            run.update(status='completed',seconds=elapsed,output=str(output),outputBytes=output.stat().st_size,outputSha256=sha256(output))
        except Exception as exc:
            run.update(error=f'{type(exc).__name__}: {exc}',seconds=time.perf_counter()-started)
        finally:
            monitor.stop.set();thread.join(timeout=2)
            if monitor.samples:
                run.update(peakVramMb=max(s.memory_used_mb for s in monitor.samples),averageGpuUtilization=round(sum(s.utilization_percent for s in monitor.samples)/len(monitor.samples),1),peakTemperatureC=max(s.temperature_c for s in monitor.samples),sampleCount=len(monitor.samples))
            report['runs'].append(run)
    provider.unload();report_path=args.report or ROOT/'benchmarks'/'reports'/f"{profile.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json";report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(f'REPORT={report_path.resolve()}')
    return 0 if all(x['status']=='completed' for x in report['runs']) else 2
if __name__=='__main__':raise SystemExit(main())
