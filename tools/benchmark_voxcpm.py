#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,platform,shutil,subprocess,sys,threading,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
if hasattr(sys.stderr, "reconfigure"):
    try: sys.stderr.reconfigure(encoding="utf-8")
    except Exception: pass
from backend.hardware import detect_nvidia_gpus
from backend.models import ModelManager
from backend.providers.voice import VoxCPM2Provider,VoiceRequest

def rtf(synthesis_seconds:float,audio_seconds:float)->float|None:return round(synthesis_seconds/audio_seconds,4) if audio_seconds>0 else None
def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
class Monitor:
 def __init__(self,index):self.index=index;self.samples=[];self.stop=threading.Event()
 def run(self):
  exe=shutil.which('nvidia-smi')
  while exe and not self.stop.is_set():
   result=subprocess.run([exe,f'--id={self.index}','--query-gpu=memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True)
   if result.returncode==0:
    try:self.samples.append(tuple(int(float(x.strip())) for x in result.stdout.strip().split(',')))
    except ValueError:pass
   self.stop.wait(.25)
def main(argv=None)->int:
 p=argparse.ArgumentParser(description='Benchmark VoxCPM2 CPU/NVIDIA streaming TTS')
 p.add_argument('--device',choices=['cpu','cuda'],default='cuda');p.add_argument('--gpu',type=int,default=0);p.add_argument('--expected-gpu');p.add_argument('--text',action='append');p.add_argument('--output-dir',type=Path,default=ROOT/'benchmarks'/'voice-outputs');p.add_argument('--report',type=Path)
 a=p.parse_args(argv);manager=ModelManager();model_id='voxcpm2'
 if not manager.is_installed(model_id):raise SystemExit('Missing voxcpm2; run: python -m backend.cli models download voxcpm2')
 gpus=detect_nvidia_gpus();gpu=None
 if a.device=='cuda':
  if a.gpu>=len(gpus):raise SystemExit(f'GPU {a.gpu} unavailable')
  gpu=gpus[a.gpu]
  if a.expected_gpu and a.expected_gpu.lower() not in gpu.name.lower():raise SystemExit(f'Expected {a.expected_gpu}, got {gpu.name}')
 entry=manager.entry(model_id);provider=VoxCPM2Provider(manager.path(model_id),device=a.device,optimize=a.device=='cuda',model_revision=entry['revision'])
 started=time.perf_counter();provider.load();load_seconds=time.perf_counter()-started;texts=a.text or ['Xin chào, đây là bài kiểm tra giọng đọc tiếng Việt.','Hello, this is an English text to speech benchmark.'];a.output_dir.mkdir(parents=True,exist_ok=True)
 report={'schemaVersion':1,'createdAt':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'python':sys.version,'device':a.device,'gpu':gpu.to_dict() if gpu else None,'modelRevision':entry['revision'],'loadSeconds':load_seconds,'runs':[]}
 for index,text in enumerate(texts,1):
  output=a.output_dir/f'voxcpm2-{a.device}-{index}.wav';events=[];monitor=Monitor(a.gpu);thread=None
  if gpu:thread=threading.Thread(target=monitor.run,daemon=True);thread.start()
  started=time.perf_counter();status='completed';error=None
  try:provider.synthesize_streaming(VoiceRequest(text,output,language='vi' if index==1 else 'en'),on_progress=events.append)
  except Exception as exc:status='failed';error=f'{type(exc).__name__}: {exc}'
  synth=time.perf_counter()-started
  if thread:monitor.stop.set();thread.join(2)
  duration=events[-1].seconds if events else 0;run={'text':text,'status':status,'synthesisSeconds':synth,'audioSeconds':duration,'rtf':rtf(synth,duration),'error':error}
  if output.exists():run.update(output=str(output),outputBytes=output.stat().st_size,outputSha256=sha256(output))
  if monitor.samples:run.update(peakVramMb=max(x[0] for x in monitor.samples),averageGpuUtilization=round(sum(x[1] for x in monitor.samples)/len(monitor.samples),1),peakTemperatureC=max(x[2] for x in monitor.samples))
  report['runs'].append(run)
 provider.unload();path=a.report or ROOT/'benchmarks'/'voice-reports'/f"voxcpm2-{a.device}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(f'REPORT={path.resolve()}');return 0 if all(x['status']=='completed' for x in report['runs']) else 2
if __name__=='__main__':raise SystemExit(main())
