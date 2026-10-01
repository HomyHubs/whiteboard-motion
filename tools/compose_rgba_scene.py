#!/usr/bin/env python3
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.services import compose_rgba_scene

def main():
 p=argparse.ArgumentParser(description='Compose separate RGBA assets and generate whiteboard annotation bounds')
 p.add_argument('manifest',type=Path);p.add_argument('--image',required=True,type=Path);p.add_argument('--annotation',required=True,type=Path)
 a=p.parse_args();result=compose_rgba_scene(a.manifest,a.image,a.annotation);print(f"elements={len(result['elements'])} warnings={len(result['warnings'])}")
if __name__=='__main__':main()
