#!/usr/bin/env python3
from preserved_source import preserved_bytes
"""Exact decoded-piece reconstruction, source locks, shared palette and budget."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib
R=Path(__file__).resolve().parents[1]
def validate_combat(root=R,files=None):
 o=root/'assets/combat-animation';m=json.loads((o/'manifest.json').read_text());pal=(root/m['palette']).read_bytes()[18:786];decoded=[];seen=set();total=0
 assert {p.name for p in o.glob('CA*.TGA')}=={p['name'] for p in m['resources']}
 assert m['slots']<255
 for p in m['resources']:
  blob=(o/p['name']).read_bytes();w,h=struct.unpack_from('<HH',blob,12);assert (w,h)==(p['width'],p['height']) and w%8==0 and h%2==0 and blob[18:786]==pal and blob[16:18]==b'\x08\0' and len(blob)==786+w*h and max(blob[786:])<254
  assert hashlib.sha256(blob).hexdigest()==p['sha256'];key=(w,h,blob[786:]);assert key not in seen;seen.add(key)
  assert p['bytes']==(w*h+31)&~31;total+=p['bytes'];im=Image.new('RGBA',(w,h));raw=blob[786:];im.putdata([(*pal[3*i:3*i+3][::-1],255) if i else (0,0,0,0) for y in range(h) for i in raw[(h-1-y)*w:(h-y)*w]]);decoded.append(im)
  if files is not None:assert files['COMBAT/'+p['name']]==blob
 def compose(parts):
  im=Image.new('RGBA',(160,112))
  for p in parts:im.alpha_composite(decoded[p['resource']],(p['x'],p['y']))
  return im
 for a,name in enumerate(['buck','chuck']):
  idle=Image.open(root/f'assets/animation-polish/{name}-00.png').convert('RGBA')
  for f,parts in enumerate(m['frames'][a]):
   native=Image.open(o/f'{name}-key-{f}.png').convert('RGBA');assert compose(parts+m['lowers'][a][0]).tobytes()==native.tobytes()
   assert native.crop((0,64,128,112)).tobytes()==idle.crop((0,48,128,96)).tobytes()
   # Every opaque original head/hair/face pixel survives exactly at its old root.
   assert all(native.getpixel((x,y+16))==idle.getpixel((x,y)) for y in range(24) for x in range(39,89) if idle.getpixel((x,y))[3])
  for f,parts in enumerate(m['lowers'][a]):
   original=idle if not f else Image.open(root/f'assets/running/{name}-{f-1}.png').convert('RGBA');got=compose(parts)
   assert got.crop((0,64,128,112)).tobytes()==original.crop((0,48,128,96)).tobytes()
 assert total==m['texture_bytes'] and m['boot_bytes']==410464+total and m['free_bytes']==458488-m['boot_bytes']>0 and m['slots']==169+len(decoded)
 # No rewritten simulation/audio/idle/walk/enemy/running sources.
 lock=json.loads((o/'source/preserved-sha256.json').read_text())
 for path,sha in lock.items():
  data=preserved_bytes(root,path)
  if path in ['src/game.c','src/game.h']:
   import re
   data=re.sub(rb'^/\* JAB BEGIN \*/\n.*?^/\* JAB END \*/\n',b'',data,flags=re.M|re.S)
  if path=='src/game.c':
   import re
   data=re.sub(rb'^/\* MOMENTUM BEGIN \*/\n.*?^/\* MOMENTUM END \*/\n',b'',data,flags=re.M|re.S)
  assert hashlib.sha256(data).hexdigest()==sha,path
 print(f"PASS combat prototype: lossless indexed reconstruction, binary alpha, immutable head/feet/alternating run legs, source locks, deduplicated {len(decoded)} strips; +{total} bytes; {m['boot_bytes']} used/{m['free_bytes']} free, {m['slots']} slots")
 return m
if __name__=='__main__':validate_combat()
