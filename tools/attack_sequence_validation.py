#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,struct,hashlib,math,subprocess
R=Path(__file__).resolve().parents[1]
def validate_sequence(root=R,files=None):
 o=root/'assets/attack-sequence';m=json.loads((o/'manifest.json').read_text());pal=(root/m['palette']).read_bytes()[18:786];total=0;ims=[];seen=set();rv=json.loads((root/'assets/running-bat-visual/manifest.json').read_text());carry=Image.open(root/'assets/running-bat-visual/carry-native.png')
 assert {p.name for p in o.glob('CA*.TGA')}=={p['name'] for p in m['resources']}
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
  low=compose(m['lowers'][a]);expected=Image.open(root/f'assets/bat-momentum/{name}-key-3.png').convert('RGBA').crop((0,64,160,112));assert low.crop((0,64,160,112)).tobytes()==expected.tobytes()
  for f,parts in enumerate(m['frames'][a]):
   upper=compose(parts);im=low.copy()
   if f>=4:
    phase=f-4;run=Image.open(root/f'assets/running/{name}-{phase}.png');assert upper.crop((0,16,128,64)).tobytes()==run.crop((0,0,128,48)).tobytes();hx,hy=rv['hands'][a][phase];im.alpha_composite(carry,(hx-24,16+hy-32))
   elif f<2:
    old=Image.open(root/f'assets/bat-momentum/{name}-key-{[1,3][f]}.png');assert upper.crop((0,0,160,64)).tobytes()==old.crop((0,0,160,64)).tobytes()
   else:
    idle=Image.open(root/f'assets/animation-polish/{name}-00.png');assert all(upper.getpixel((x,y+16))==idle.getpixel((x,y)) for y in range(24) for x in range(39,89) if idle.getpixel((x,y))[3])
   im.alpha_composite(upper);assert im.tobytes()==Image.open(o/f'{name}-key-{f}.png').convert('RGBA').tobytes()
   assert sum(im.getpixel((x,63))[3]>0 and im.getpixel((x,64))[3]>0 for x in range(160))>=10,(name,f,'waist seam')
 # Unwrapped screen-space angles decrease: physical counterclockwise for right-facing.
 observations=json.loads((o/'arc-observations.json').read_text())
 from attack_sequence_previews import render
 for a,actor in enumerate(observations):
  angles=[p['angle'] for p in actor]
  assert all(-180<b-a<0 for a,b in zip(angles,angles[1:])),angles
  assert all(33<=p['length']<=38 for p in actor) and max(p['length'] for p in actor)-min(p['length'] for p in actor)<=3,actor
  for index,p in enumerate(actor):
   key,weapon=[(4,0),(4,1),(4,2),(2,-1),(1,-1),(3,-1)][index];im=render(a,key,weapon);assert im.getpixel(tuple(p['grip']))[3] and im.getpixel(tuple(p['tip']))[3]
   gx,gy=p['grip'];tx,ty=p['tip'];vx,vy=tx-gx,ty-gy;length=math.hypot(vx,vy);nodes={(x,y) for y in range(max(0,min(gy,ty)-6),min(112,max(gy,ty)+7)) for x in range(max(0,min(gx,tx)-6),min(160,max(gx,tx)+7)) if im.getpixel((x,y))[3] and abs((x-gx)*vy-(y-gy)*vx)/length<=6};todo=[(gx,gy)];visited=set(todo)
   while todo:
    x,y=todo.pop()
    for dx in [-1,0,1]:
     for dy in [-1,0,1]:
      q=(x+dx,y+dy)
      if q in nodes and q not in visited:visited.add(q);todo.append(q)
   assert (tx,ty) in visited,(a,index,'disconnected grip/blade')
  for p in actor:assert abs(math.degrees(math.atan2(p['tip'][1]-p['grip'][1],p['tip'][0]-p['grip'][0]))-((p['angle']+180)%360-180))<0.001
 assert total==m['texture_bytes'] and m['boot_bytes']==410464+total and m['free_bytes']==458488-m['boot_bytes']>=0 and m['slots']==169+len(ims)<255
 print(f"PASS sequence bank: exact jab/impact/carry uppers, clean fixed legs, native head/waist locks, counterclockwise arc, shared indexed palette; {m['boot_bytes']} used/{m['free_bytes']} free/{m['slots']} slots")
 return m
if __name__=='__main__':validate_sequence()
