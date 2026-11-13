#!/usr/bin/env python3
"""Create review sheets from decoded native RGB555 pixels (nearest-neighbor)."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json, numpy as np
R=Path(__file__).resolve().parents[1];O=R/'docs/ricky-rose-preview';m=json.loads((R/'assets/ricky/manifest.json').read_text());regions=json.loads((R/'art/ricky/rose-regions.json').read_text())
def decode(path):
 b=path.read_bytes();w=int.from_bytes(b[12:14],'little');h=int.from_bytes(b[14:16],'little');pal=[tuple((v>>3)*255//31 for v in b[i:i+3][::-1])+(255,) for i in range(18,786,3)];pal[0]=(0,0,0,0);im=Image.new('RGBA',(w,h));im.putdata([pal[v] for v in b[786:]]);return im
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
except OSError:font=ImageFont.load_default()
# Each panel shows full native payloads at 1x and nearest-neighbor 3x, before/after.
full=Image.new('RGB',(1500,5*420),(30,39,42));d=ImageDraw.Draw(full)
close=Image.new('RGB',(1500,5*230),(30,39,42));dc=ImageDraw.Draw(close)
for i,f in enumerate(m['frames']):
 before=decode(R/f'art/ricky/runtime-original/RK{i:02}.TGA');after=decode(R/f'assets/ricky/RK{i:02}.TGA');after.save(O/'native'/(f['name']+'.png'))
 x=i%5*300;y=i//5*420;d.text((x+10,y+8),f['name']+'   BEFORE / AFTER',font=font,fill='white')
 for j,im in enumerate((before,after)):
  px=x+j*150;full.paste(im,(px+18,y+120-f['anchor'][1]),im)
  big=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
  # Wide extended-chain pose fits its full silhouette at 2x within pair panel.
  if big.width>148:big=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  if big.width>148:big=im.resize((im.width,im.height),Image.Resampling.NEAREST)
  full.paste(big,(px+(150-big.width)//2,y+410-big.height),big)
 # Project source region into the locked native anchor/crop coordinate system.
 x0,y0,x1,y1=f['source_box'];scale=f['scale'];left=round((f['root'][0]-x0)*scale)-f['anchor'][0];top=round((f['root'][1]-y0)*scale)-f['anchor'][1]
 poly=regions[f['name']];xs=[round((v[0]-x0)*scale)-left for v in poly];ys=[round((v[1]-y0)*scale)-top for v in poly]
 cx=(min(xs)+max(xs))//2;cy=(min(ys)+max(ys))//2;box=(cx-10,cy-11,cx+11,cy+12)
 xx=i%5*300;yy=i//5*230;dc.text((xx+10,yy+8),f['name'],font=font,fill='white')
 for j,im in enumerate((before,after)):
  q=im.crop(box).resize((126,138),Image.Resampling.NEAREST);close.paste(q,(xx+10+j*145,yy+55),q);dc.text((xx+10+j*145,yy+32),'BEFORE' if not j else 'AFTER',font=font,fill='#cdd8d8')
 arr=np.array(after);visible=arr[:,:,3]>0;red=(arr[:,:,0].astype(int)>arr[:,:,1].astype(int)*1.5)&(arr[:,:,0].astype(int)>arr[:,:,2].astype(int)*1.3)&visible;green=(arr[:,:,1]>arr[:,:,0])&(arr[:,:,1]>arr[:,:,2])&visible
 print(f['name'], 'green',int(green.sum()),'red',int(red.sum()))
full.save(O/'all-25-before-after.png');close.save(O/'all-25-shoulder-closeups.png')
