import json,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from backend.services.rgba_scene import alpha_bounds,compose_rgba_scene
class RgbaSceneTests(unittest.TestCase):
 def test_alpha_bounds(self):
  image=Image.new('RGBA',(20,20),(0,0,0,0));ImageDraw.Draw(image).rectangle((3,4,10,12),fill=(0,0,0,255));self.assertEqual(alpha_bounds(image),(3,4,11,13))
 def test_compose_and_annotation(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);asset=Image.new('RGBA',(20,20),(0,0,0,0));ImageDraw.Draw(asset).rectangle((2,3,9,14),fill=(255,0,0,255));asset.save(root/'a.png')
   manifest={'sceneId':'s','canvas':{'width':100,'height':80},'assets':[{'id':'a','path':'a.png','x':10,'y':20,'sequence':1}]};(root/'m.json').write_text(json.dumps(manifest))
   result=compose_rgba_scene(root/'m.json',root/'scene.png',root/'scene.annotation.json');self.assertEqual(result['elements'][0]['region'],{'x':12,'y':23,'width':8,'height':12});self.assertTrue((root/'scene.png').exists())
