#!/usr/bin/env python3
"""Register the targeted edit guide, clean clusters and quantize to locked CP palette.
Output source poses are reviewed native artwork, not a runtime scaling operation.
"""
from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np
from collections import deque
R=Path(__file__).resolve().parents[1];O=R/'assets/corporate-punk-hq-combat';B=R/'assets/corporate-punk-lighting'
pal=(B/'palette.bgr24').read_bytes();rgb=np.array([list(pal[i:i+3][::-1]) for i in range(0,768,3)],dtype=np.int32)
guide=Image.open(O/'source/combat-pose-edit-guide.png').convert('RGB').resize((432,256),Image.Resampling.NEAREST)
master=Image.open(B/'idle-0.png').convert('RGBA');native=Image.new('RGBA',(144,112));native.alpha_composite(master,(16,16));native.save(O/'ready.png')
def indexed(q):
 a=np.asarray(q);px=a[:,:,:3].astype(np.int32);out=Image.new('P',q.size);out.putpalette(rgb.flatten().tolist());raw=[]
 for y in range(q.height):
  for x in range(q.width):raw.append(0 if not a[y,x,3] else int(np.argmin(((rgb[1:254]-px[y,x])**2).sum(axis=1)))+1)
 out.putdata(raw);out.info['transparency']=0;return out
for i,name in [(2,'strike'),(3,'hurt'),(4,'fall'),(5,'ground')]:
 x=i%3*144;y=i//3*128;q=guide.crop((x,y,x+144,y+108));a=np.asarray(q).astype(np.int32);bg=np.array([12,16,25]);mask=((a-bg)**2).sum(axis=2)>500;mask &= a.max(axis=2)>32
 # Keep the largest connected colored silhouette, then enclose internal dark suit clusters.
 seen=set();parts=[]
 for yy,xx in zip(*np.where(mask)):
  if (xx,yy) in seen:continue
  todo=[(xx,yy)];seen.add((xx,yy));part=[]
  while todo:
   xx1,yy1=todo.pop();part.append((xx1,yy1))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    z=(xx1+dx,yy1+dy)
    if 0<=z[0]<144 and 0<=z[1]<108 and mask[z[1],z[0]] and z not in seen:seen.add(z);todo.append(z)
  parts.append(part)
 mask=np.zeros((108,144),dtype=np.uint8)
 # Nearby highlights may be disconnected by dark outline: retain nontrivial components.
 for part in parts:
  if len(part)>=4:
   for xx,yy in part:mask[yy,xx]=255
 alpha=Image.fromarray(mask).filter(ImageFilter.MaxFilter(3));m=np.array(alpha)>0;outside=set();todo=deque([(0,0)])
 while todo:
  xx,yy=todo.popleft()
  if not(0<=xx<144 and 0<=yy<108) or m[yy,xx] or (xx,yy) in outside:continue
  outside.add((xx,yy));todo.extend([(xx+1,yy),(xx-1,yy),(xx,yy+1),(xx,yy-1)])
 for yy in range(108):
  for xx in range(144):
   if (xx,yy) not in outside:mask[yy,xx]=255
 q=q.convert('RGBA');q.putalpha(Image.fromarray(mask));out=Image.new('RGBA',(144,112));out.alpha_composite(q)
 if name=='strike':
  # Exact master head/hair and existing pelvis/leg pieces stay native and registered.
  out.paste((0,0,0,0),(0,0,144,38));out.alpha_composite(master.crop((0,0,96,22)),(16,16))
  # Keep the visible fist near the unchanged 40px attack reach.
  arm=out.copy();out.paste((0,0,0,0),(90,38,144,60));out.alpha_composite(arm.crop((98,38,144,60)),(90,38))
  out.paste((0,0,0,0),(0,68,144,112));out.alpha_composite(master.crop((0,52,96,96)),(16,68))
 else:
  # Grounded soles terminate at the same y108 baseline; fall is intentionally airborne.
  if name in ['hurt','ground']:
   box=out.getbbox();shift=108-box[3];temp=Image.new('RGBA',out.size);temp.alpha_composite(out,(0,shift));out=temp
 # Local native corrections after guide isolation: preserve complete pointed shoes.
 if name=='hurt':
  from PIL import ImageDraw
  out.paste((0,0,0,0),(0,92,144,112));out.alpha_composite(master.crop((0,76,96,92)),(16,92))
  draw=ImageDraw.Draw(out);draw.polygon([(41,89),(47,89),(44,98),(39,98)],fill=master.getpixel((30,70)))
  # Restore texture on the ankle join using existing trouser colors, not a new palette.
  for yy in range(90,96):
   for xx in range(40,45):
    if out.getpixel((xx,yy))[3]:out.putpixel((xx,yy),master.getpixel((30+(xx-40),70+(yy-90))))
 if name=='ground':
  # Correct the edit guide's overlong horizontal torso/leg spans; head remains untouched.
  cuts=set(range(48,56))|set(range(82,90))|set(range(118,126))
  temp=Image.new('RGBA',out.size);tx=12
  for sx in range(144):
   if sx in cuts:continue
   if tx<144:temp.paste(out.crop((sx,0,sx+1,112)),(tx,0))
   tx+=1
  out=temp
 indexed(out).save(O/f'{name}.png',transparency=0)
indexed(native).save(O/'ready.png',transparency=0)
