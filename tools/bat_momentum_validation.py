#!/usr/bin/env python3
"""New bank only: exact assembly, per-pose registration and planted limb mask."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib
R=Path(__file__).resolve().parents[1]
def validate_momentum(root=R,files=None):
 o=root/'assets/bat-momentum';m=json.loads((o/'manifest.json').read_text());pal=(root/m['palette']).read_bytes()[18:786];ims=[];seen=set();total=0
 assert {p.name for p in o.glob('CA*.TGA')}=={p['name'] for p in m['resources']} and m['slots']<255
 for p in m['resources']:
  blob=(o/p['name']).read_bytes();w,h=struct.unpack_from('<HH',blob,12);assert (w,h)==(p['width'],p['height']) and w%8==0 and h%2==0 and blob[18:786]==pal and blob[16:18]==b'\x08\0' and len(blob)==786+w*h and max(blob[786:])<254
  assert hashlib.sha256(blob).hexdigest()==p['sha256'];key=(w,h,blob[786:]);assert key not in seen;seen.add(key);total+=p['bytes'];assert p['bytes']==(w*h+31)&~31
  im=Image.new('RGBA',(w,h));raw=blob[786:];im.putdata([(*pal[3*i:3*i+3][::-1],255) if i else (0,0,0,0) for y in range(h) for i in raw[(h-1-y)*w:(h-y)*w]]);ims.append(im)
  if files is not None:assert files['COMBAT/'+p['name']]==blob
 def compose(parts):
  out=Image.new('RGBA',(160,112))
  for p in parts:out.alpha_composite(ims[p['resource']],(p['x'],p['y']))
  return out
 for a,name in enumerate(['buck','chuck']):
  assert len(m['lowers'][a])==2
  old=[Image.open(root/f'assets/combat-animation/{name}-key-{f}.png').convert('RGBA') for f in range(4)];new=[Image.open(o/f'{name}-key-{f}.png').convert('RGBA') for f in range(4)]
  for f in range(4):
   lower=m['lowers'][a][int(f>=2)];assert compose(m['frames'][a][f]+lower).tobytes()==new[f].tobytes()
   if f<2:assert old[f].tobytes()==new[f].tobytes()
  assert old[2].crop((0,0,160,64)).tobytes()==new[2].crop((0,0,160,64)).tobytes()
  # The entire arm/hand/bat/torso geometry is translated by exactly20 pixels;
  # no independent hand or weapon transform, no body rescaling.
  assert old[3].crop((0,40,140,64)).tobytes()==new[3].crop((20,40,160,64)).tobytes()
  idle=Image.open(root/f'assets/animation-polish/{name}-00.png').convert('RGBA')
  for f in [2,3]:
   assert all(new[f].getpixel((x,y+16))==idle.getpixel((x,y)) for y in range(24) for x in range(39,89) if idle.getpixel((x,y))[3])
  before=old[2].crop((0,64,128,112));after=new[2].crop((0,64,128,112));removed=0
  for x in range(128):
   for y in range(48):
    p,q=before.getpixel((x,y)),after.getpixel((x,y))
    if p!=q:assert p[3] and not q[3];removed+=1
  assert removed==[18,120][a]
  assert new[2].crop((0,64,128,112)).tobytes()==new[3].crop((0,64,128,112)).tobytes()
  # A continuous opaque waist overlap at the exact upper/lower join, not merely
  # matching bounding boxes or filename assumptions.
  for f in [2,3]:assert sum(new[f].getpixel((x,63))[3]>0 and new[f].getpixel((x,64))[3]>0 for x in range(160))>=12
 assert total==m['texture_bytes'] and m['boot_bytes']==410464+total and m['free_bytes']==458488-m['boot_bytes']>0 and m['slots']==169+len(ims)
 print(f"PASS planted bank: 20px contact registration, exact head/hand/weapon source pixels, 18/120 detached cuff/glove pixels removed, fixed connected lower stance, unchanged punches/palette; {m['boot_bytes']} used/{m['free_bytes']} free, {m['slots']} slots")
 return m
if __name__=='__main__':validate_momentum()
