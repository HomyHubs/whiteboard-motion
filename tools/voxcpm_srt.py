#!/usr/bin/env python3
from __future__ import annotations
import argparse,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from backend.cache import AudioCache
from backend.hardware import detect_nvidia_gpus
from backend.models import ModelManager
from backend.providers.voice import VoxCPM2Provider
from backend.services import generate_timeline_clips
from parse_srt import parse_srt
from tts_narration import build_track,mux,retime_cues,write_srt,probe_duration,FFMPEG,FFPROBE

def main(argv=None)->int:
 p=argparse.ArgumentParser(description='SRT -> VoxCPM2 local voice timeline')
 p.add_argument('srt',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto');p.add_argument('--language',choices=['vi','en'],default='vi');p.add_argument('--reference-audio',type=Path);p.add_argument('--reference-text',default='');p.add_argument('--confirm-voice-consent',action='store_true');p.add_argument('--retime-out',type=Path);p.add_argument('--gap',type=float,default=.3);p.add_argument('--pause',action='append',default=[]);p.add_argument('--tail',type=float,default=1.0);p.add_argument('--video',type=Path);p.add_argument('--video-out',type=Path)
 a=p.parse_args(argv)
 if not (shutil.which(FFMPEG) or Path(FFMPEG).is_file()) or not (shutil.which(FFPROBE) or Path(FFPROBE).is_file()):raise SystemExit('ffmpeg/ffprobe are required (bundled, WHITEBOARD_FFMPEG_DIR or PATH)')
 if a.reference_audio and not a.confirm_voice_consent:raise SystemExit('Voice clone requires --confirm-voice-consent')
 device=('cuda' if detect_nvidia_gpus() else 'cpu') if a.device=='auto' else a.device;m=ModelManager();entry=m.entry('voxcpm2')
 if not m.is_installed('voxcpm2'):raise SystemExit('Missing voxcpm2; run models download voxcpm2')
 cues=[c for c in parse_srt(a.srt.read_text(encoding='utf-8-sig')) if c['text']]
 if not cues:raise SystemExit('No SRT cues found')
 cache=AudioCache(a.srt.parent/'voxcpm-cache');provider=VoxCPM2Provider(m.path('voxcpm2'),device=device,optimize=device=='cuda',cache=cache,model_revision=entry['revision'])
 clips=generate_timeline_clips(cues,provider,a.srt.parent/'voxcpm-cues',a.language,a.reference_audio,a.reference_text,a.confirm_voice_consent,on_progress=lambda x:print(f"[{x.cue_index}/{x.cue_count}] {x.message}"))
 if a.retime_out:
  try:pauses={int(k):float(v) for k,v in (x.split('=',1) for x in a.pause)}
  except ValueError:raise SystemExit('--pause format: INDEX=SECONDS')
  cues=retime_cues(cues,clips,a.gap,pauses,a.tail);write_srt(cues,a.retime_out);print(f'SRT={a.retime_out.resolve()}')
 total_ms=int(probe_duration(a.video)*1000) if a.video else None;build_track(cues,clips,a.output,total_ms);print(f'AUDIO={a.output.resolve()}')
 if a.video:
  video_out=a.video_out or a.video.with_name(a.video.stem+'-voxcpm.mp4');mux(a.video,a.output,video_out);print(f'OUTPUT={video_out.resolve()}')
 provider.unload();return 0
if __name__=='__main__':raise SystemExit(main())
