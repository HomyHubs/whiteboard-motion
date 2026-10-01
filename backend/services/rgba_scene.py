from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class Bounds:
    x:int;y:int;width:int;height:int
    def as_region(self)->dict:return {"x":self.x,"y":self.y,"width":self.width,"height":self.height}

def alpha_bounds(image,threshold:int=8)->tuple[int,int,int,int]|None:
    if image.mode!='RGBA':image=image.convert('RGBA')
    alpha=image.getchannel('A').point(lambda value:255 if value>=threshold else 0)
    return alpha.getbbox()

def intersects(a:Bounds,b:Bounds)->bool:
    return a.x < b.x+b.width and a.x+a.width > b.x and a.y < b.y+b.height and a.y+a.height > b.y

def compose_rgba_scene(manifest_path:Path,output_image:Path,output_annotation:Path)->dict[str,Any]:
    try:from PIL import Image
    except ImportError as exc:raise RuntimeError('Pillow is required') from exc
    data=json.loads(manifest_path.read_text(encoding='utf-8'));canvas=data.get('canvas') or {};width=int(canvas['width']);height=int(canvas['height']);background=canvas.get('background','#F5EBD7')
    base=Image.new('RGBA',(width,height),background);elements=[];warnings=[];regions=[];base_dir=manifest_path.parent
    assets=sorted(data.get('assets',[]),key=lambda item:int(item.get('sequence',0)))
    for index,item in enumerate(assets,1):
        path=Path(item['path']);path=path if path.is_absolute() else base_dir/path
        image=Image.open(path).convert('RGBA')
        scale=float(item.get('scale',1.0))
        if scale<=0:raise ValueError(f"Asset {path} has invalid scale")
        if scale!=1:image=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.LANCZOS)
        bbox=alpha_bounds(image,int(item.get('alphaThreshold',8)))
        if bbox is None:warnings.append(f"Asset transparent: {path}");continue
        x,y=int(item.get('x',0)),int(item.get('y',0));left,top,right,bottom=bbox;region=Bounds(x+left,y+top,right-left,bottom-top)
        if region.x<0 or region.y<0 or region.x+region.width>width or region.y+region.height>height:raise ValueError(f"Asset outside canvas: {path} -> {region}")
        for previous_id,previous in regions:
            if intersects(previous,region):warnings.append(f"Overlap: {previous_id} <-> {item.get('id',path.stem)}")
        base.alpha_composite(image,(x,y));regions.append((item.get('id',path.stem),region))
        reveal=item.get('reveal') or {};start=int(reveal.get('startMs',(index-1)*3000));duration=int(reveal.get('durationMs',3000));sequence=int(item.get('sequence',index))
        elements.append({"id":item.get('id',path.stem),"label":item.get('label',path.stem),"sequence":sequence,"narrativeRole":item.get('narrativeRole',''),"subtitle":item.get('subtitle',''),"sourceAsset":str(path),"region":region.as_region(),"reveal":{"direction":reveal.get('direction','top_to_bottom'),"startMs":start,"durationMs":duration,"maskPaddingPx":int(reveal.get('maskPaddingPx',0)),"protectedRegions":reveal.get('protectedRegions',[])},"handPath":{"start":[region.x+region.width//2,region.y],"end":[region.x+region.width//2,region.y+region.height-1],"easing":"easeInOut"}})
    output_image.parent.mkdir(parents=True,exist_ok=True);base.convert('RGB').save(output_image)
    annotation={"sceneId":data.get('sceneId',output_image.stem),"canvas":{"width":width,"height":height},"storyBasis":data.get('storyBasis',''),"sceneDurationMs":int(data.get('sceneDurationMs',max((e['reveal']['startMs']+e['reveal']['durationMs'] for e in elements),default=1000)+1000)),"elements":elements,"warnings":warnings}
    output_annotation.parent.mkdir(parents=True,exist_ok=True);output_annotation.write_text(json.dumps(annotation,ensure_ascii=False,indent=2),encoding='utf-8')
    return annotation
