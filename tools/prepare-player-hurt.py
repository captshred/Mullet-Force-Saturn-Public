#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import json,struct,hashlib
R=Path(__file__).resolve().parents[1];O=R/'assets/player-hurt';pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=np.array([list(pal[i:i+3][::-1]) for i in range(0,768,3)],dtype=np.int32)
def quant(im):
 a=np.asarray(im);q=Image.new('P',im.size);q.putpalette(colors.flatten().tolist());q.putdata([0 if not c[3] else int(np.argmin(((colors[1:254]-c[:3])**2).sum(axis=1)))+1 for row in a.astype(np.int32) for c in row]);q.info['transparency']=0;return q
source=Image.open(O/'source/hurt-edit-guide.png').convert('RGB').resize((512,224),Image.Resampling.NEAREST)
for a,n in enumerate(['buck','chuck']):
 master=Image.open(R/f'assets/animation-polish/{n}-00.png').convert('RGBA');poses=[]
 for f in range(3):
  q=source.crop(((f+1)*128,a*112,(f+2)*128,a*112+96));v=np.asarray(q).astype(np.int32);mask=(((v-np.array([16,20,32]))**2).sum(axis=2)>160).astype(np.uint8)*255
  q=q.convert('RGBA');q.putalpha(Image.fromarray(mask));# Delete only disconnected background specks, never interior suit/boot pixels.
  seen=set()
  for y in range(96):
   for x in range(128):
    if not q.getpixel((x,y))[3] or (x,y) in seen:continue
    todo=[(x,y)];part=[];seen.add((x,y))
    while todo:
     xx,yy=todo.pop();part.append((xx,yy))
     for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
      z=(xx+dx,yy+dy)
      if 0<=z[0]<128 and 0<=z[1]<96 and z not in seen and q.getpixel(z)[3]:seen.add(z);todo.append(z)
    if len(part)<5:
     for z in part:q.putpixel(z,(0,0,0,0))
  # Exact original standing lower body on initial recoil, no change to native root.
  if f==0:q.paste((0,0,0,0),(0,48,128,96));q.alpha_composite(master.crop((0,48,128,96)),(0,48))
  if f==0:
   # Remove disconnected old guard cuff/hand fragments introduced by the reused lower band.
   groups=[];seen2=set()
   for yy in range(96):
    for xx in range(128):
     if (xx,yy) in seen2 or not q.getpixel((xx,yy))[3]:continue
     todo=[(xx,yy)];seen2.add((xx,yy));group=[]
     while todo:
      vx,vy=todo.pop();group.append((vx,vy))
      for dx in [-1,0,1]:
       for dy in [-1,0,1]:
        z=(vx+dx,vy+dy)
        if 0<=z[0]<128 and 0<=z[1]<96 and z not in seen2 and q.getpixel(z)[3]:seen2.add(z);todo.append(z)
     groups.append(group)
   keep=max(groups,key=len)
   for group in groups:
    if group is not keep:
     for z in group:q.putpixel(z,(0,0,0,0))
  poses.append(q)
 # Pain and gimpy recovery share one coherent lower body, including the hanging hand.
 poses[2].paste(poses[1].crop((0,52,128,96)),(0,52))
 # Match the hanging forearm to its shared wrist at the y52 seam.
 poses[2].paste(poses[1].crop((82,43,104,52)),(82,43))
 for f,q in enumerate(poses):
  if n=='buck' and f>0:
   registered=Image.new('RGBA',q.size);registered.alpha_composite(q,(0,-1));q=registered
  quant(q).save(O/f'{n}-hurt-{f}.png',transparency=0)
# Authoritative run fix: only the obsolete large front-swing arm in Chuck pose 3.
old=Image.open(R/'assets/running/chuck-2.png').convert('RGBA');donor=Image.open(R/'assets/running/chuck-0.png').convert('RGBA');new=old.copy();mask=Image.new('1',old.size);d=ImageDraw.Draw(mask);d.polygon([(60,22),(66,22),(70,29),(78,32),(86,32),(88,36),(85,41),(66,44),(60,38)],fill=1)
for y in range(96):
 for x in range(128):
  if not mask.getpixel((x,y)) or (x>=85 and y<=33):continue
  c=donor.getpixel((x-2,y)) if x<77 else Image.open(R/'assets/running/chuck-1.png').convert('RGBA').getpixel((x-2,y-2))
  if x<68 and c[0]>c[2]*1.25 and c[0]>c[1]*1.1:c=donor.getpixel((62+x%3,28+y%8))
  new.putpixel((x,y),c)
new.save(O/'chuck-run-2-clean.png');mask.save(O/'source/obsolete-arm-region.png');changed=[]
for y in range(96):
 for x in range(128):
  if old.getpixel((x,y))!=new.getpixel((x,y)):changed.append([x,y])
(O/'source/run-changed-pixels.json').write_text(json.dumps(changed)+'\n')
# Same dimensions and positions as RN18/19; no new run definitions or bytes.
m=json.loads((R/'assets/running/manifest.json').read_text());parts=m['actors'][1]['frames'][2]['parts']
for k,p in enumerate(parts[:2]):
 orig=R/f'assets/running/RN{p["resource"]-81:02}.TGA';b=orig.read_bytes();w,h=struct.unpack_from('<HH',b,12);q=new.crop((p['x'],p['y'],p['x']+w,p['y']+h));indexed=quant(q);raw=bytearray(b[786:])
 for xx,yy in changed:
  tx,ty=xx-p['x'],yy-p['y']
  if 0<=tx<w and 0<=ty<h:raw[(h-1-ty)*w+tx]=indexed.getpixel((tx,ty))
 (O/f'RC{k}.TGA').write_bytes(b[:786]+bytes(raw))
seq=json.loads((R/'assets/attack-sequence/manifest.json').read_text())
for k,p in enumerate(seq['frames'][1][6][1:]):
 b=(R/'assets/attack-sequence'/seq['resources'][p['resource']]['name']).read_bytes();w,h=struct.unpack_from('<HH',b,12);raw=bytearray(b[786:]);indexed=quant(new)
 for xx,yy in changed:
  tx,ty=xx-p['x'],yy+16-p['y']
  if 0<=tx<w and 0<=ty<h:raw[(h-1-ty)*w+tx]=indexed.getpixel((xx,yy))
 (O/f'CT{k}.TGA').write_bytes(b[:786]+bytes(raw))
