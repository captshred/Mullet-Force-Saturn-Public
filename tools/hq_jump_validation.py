#!/usr/bin/env python3
from preserved_source import preserved_bytes
from pathlib import Path
from PIL import Image
import json,struct,hashlib
from hq_jump_previews import render
R=Path(__file__).resolve().parents[1]
def validate_hq_jump(root=R,files=None):
 m=json.loads((root/'assets/hq-jump/manifest.json').read_text());seen=set();pal=(root/'assets/gallery/GB0.TGA').read_bytes()[18:786]
 for path,sha in json.loads((root/'assets/hq-jump/preserved-sha256.json').read_text()).items():assert hashlib.sha256(preserved_bytes(root,path)).hexdigest()==sha,path
 for p in m['resources']:
  b=(root/'assets/hq-jump'/p['name']).read_bytes();assert hashlib.sha256(b).hexdigest()==p['sha256'];assert struct.unpack_from('<HH',b,12)==(p['width'],p['height']);assert b[18:786]==pal and max(b[786:])<254;assert p['width']%8==0 and p['height']%2==0;assert p['bytes']==(p['width']*p['height']+31)&~31;assert b not in seen;seen.add(b)
  if files is not None:assert files['HQJUMP/'+p['name']]==b
 for a,n in enumerate(['buck','chuck']):
  idle=Image.open(root/f'assets/animation-polish/{n}-00.png').convert('RGBA')
  for k in [2,3,4,6]:
   im=render(a,k);assert im.crop((0,16,128,40)).tobytes()==idle.crop((0,0,128,24)).tobytes(),(n,k,'head changed')
   # Connected silhouette has one head, torso/pelvis and both complete legs.
   nodes={(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]};parts=[]
   while nodes:
    q=nodes.pop();todo=[q];part={q}
    while todo:
     x,y=todo.pop()
     for dx in [-1,0,1]:
      for dy in [-1,0,1]:
       v=x+dx,y+dy
       if v in nodes:nodes.remove(v);part.add(v);todo.append(v)
    parts.append(part)
   body=max(parts,key=len);assert len(body)>len(set.union(*parts))*.98,(n,k,'detached pieces',list(map(len,parts)))
   assert min(y for x,y in body)<=22 and max(y for x,y in body)>=70
  for k in [1,5]:
   im=render(a,k);assert im.crop((0,96,128,112)).tobytes()==idle.crop((0,80,128,96)).tobytes(),(n,k,'moved grounded boots')
  assert len({render(a,k).tobytes() for k in range(7)})==7
 legacy=json.loads((root/'assets/manifest.json').read_text())['assets'];names={f'{prefix}{f:02}.TGA' for prefix in ['BU','CH','NL'] for f in [11,12,14]};assert sum((p['vram']+31)&~31 for p in legacy if p['name'] in names)==m['replaced_bytes']
 assert sum(p['bytes'] for p in m['resources'])==m['texture_bytes'];assert m['boot_bytes']==454400-22784+m['texture_bytes'];assert m['free_bytes']==458488-m['boot_bytes']>0;assert m['slots']==244-9+len(m['resources'])+5<=255 and m['palette_banks_added']==0
 print(f"PASS HQ jump: exact head pixels and ground boots, distinct connected poses, shared indexed palette, old gameplay/audio/torch locks; {m['boot_bytes']} used/{m['free_bytes']} free/{m['slots']} definitions")
 if (root/'assets/hq-jump-anatomy/preserved-sha256.json').exists():
  from hq_jump_anatomy import validate
  validate()
 return m
if __name__=='__main__':validate_hq_jump()
