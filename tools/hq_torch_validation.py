#!/usr/bin/env python3
from preserved_source import preserved_bytes
from pathlib import Path
from PIL import Image
import json,struct,hashlib
from hq_torch_previews import render,decode
R=Path(__file__).resolve().parents[1]
def validate_hq_torch(root=R,files=None):
 m=json.loads((root/'assets/hq-torch/manifest.json').read_text());seen=set()
 for path,sha in json.loads((root/'assets/hq-torch/preserved-sha256.json').read_text()).items():assert hashlib.sha256(preserved_bytes(root,path)).hexdigest()==sha,path
 for p in m['resources']:
  blob=(root/'assets/hq-torch'/p['name']).read_bytes();assert hashlib.sha256(blob).hexdigest()==p['sha256'];assert struct.unpack_from('<HH',blob,12)==(p['width'],p['height']);assert max(blob[786:])<254;assert p['width']%8==0;assert p['bytes']==(p['width']*p['height']+31)&~31
  pal=root/('assets/gallery/GB0.TGA' if p['palette']==0 else 'assets/corporate-punk-lighting/CP00.TGA');assert blob[18:786]==pal.read_bytes()[18:786];assert blob not in seen;seen.add(blob)
  if files is not None:assert files['HQTORCH/'+p['name']]==blob
 for a,n in enumerate(['buck','chuck']):
  idle=Image.open(root/f'assets/animation-polish/{n}-00.png').convert('RGBA')
  for pose in range(3):
   im=render(a,pose,flame=None);assert im.crop((0,16,128,40)).tobytes()==idle.crop((0,0,128,24)).tobytes(),(n,pose,'head changed')
   assert im.crop((0,96,128,112)).tobytes()==idle.crop((0,80,128,96)).tobytes(),(n,pose,'boots moved')
   assert render(a,pose,flame=None,flip=True).tobytes()==im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
  for w in range(3):
   im=render(a,0,w);assert im.getbbox()[3]==108
  # Flame begins at original root+34, height40; nozzle pixel is adjacent.
  fire=render(a,1);assert fire.getpixel((98,68))[3]
 assert sum(p['bytes'] for p in m['resources'])==m['texture_bytes'];assert m['boot_bytes']==457632-16320+m['texture_bytes'];assert m['free_bytes']==458488-m['boot_bytes']>0;assert m['slots']==229-6+len(m['resources'])+9<255
 assert m['palette_banks_added']==0
 print(f"PASS HQ torch: exact approved heads/boots, mirrored native assemblies, indexed shared palettes, {m['boot_bytes']} used/{m['free_bytes']} free/{m['slots']} slots")
 return m
if __name__=='__main__':validate_hq_torch()
