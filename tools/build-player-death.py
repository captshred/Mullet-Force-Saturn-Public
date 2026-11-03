#!/usr/bin/env python3
"""Deterministic native registration, exact approved upper reuse, indexed packing."""
from pathlib import Path
from PIL import Image
import numpy as np
import json,struct,hashlib
R=Path(__file__).resolve().parents[1];O=R/'assets/player-death';H=R/'assets/player-hurt'
pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=np.array([list(pal[i:i+3][::-1]) for i in range(0,768,3)],dtype=np.int32)
def quant(im):
 a=np.asarray(im).astype(np.int32);q=Image.new('P',im.size);q.putpalette(colors.flatten().tolist());q.putdata([0 if not c[3] else int(np.argmin(((colors[1:254]-c[:3])**2).sum(axis=1)))+1 for row in a for c in row]);q.info['transparency']=0;return q
res=[];pieces=[]
guide=Image.open(O/'source/kneel-edit-guide.png').convert('RGB').resize((1024,448),Image.Resampling.NEAREST)
for a,n in enumerate(['buck','chuck']):
 crop=guide.crop((768,a*224,1024,a*224+192)).resize((128,96),Image.Resampling.NEAREST).convert('RGBA');v=np.asarray(crop);mask=~((v[:,:,2].astype(int)>v[:,:,1].astype(int)+3)&(v[:,:,1]>v[:,:,0])&(np.max(v[:,:,:3],axis=2)<48));crop.putalpha(Image.fromarray((mask*255).astype(np.uint8)))
 # Only generated lower anatomy is used. Identity, upper body and approved hurt art are exact.
 out=Image.new('RGBA',(128,96));upper=Image.open(H/f'{n}-hurt-2.png').convert('RGBA').crop((0,0,128,52));out.alpha_composite(upper,(0,14));out.alpha_composite(crop.crop((0,65,128,91)),(0,66));q=quant(out);q.save(O/f'{n}-collapse.png',transparency=0)
 low=q.copy();low.paste(0,(0,0,128,66));x,y,right,bottom=low.getbbox();w=(right-x+7)//8*8;h=(bottom-y+1)//2*2
 raw=bytes(low.getpixel((xx,yy)) if xx<128 and yy<96 else 0 for yy in range(y+h-1,y-1,-1) for xx in range(x,x+w));hd=bytearray(18);hd[1:3]=b'\1\1';struct.pack_into('<H',hd,5,256);hd[7]=24;struct.pack_into('<HH',hd,12,w,h);hd[16]=8;name=f'PD{a}.TGA';blob=bytes(hd)+pal+raw;(O/name).write_bytes(blob);res.append(dict(name=name,width=w,height=h,bytes=(w*h+31)&~31,sha256=hashlib.sha256(blob).hexdigest()));pieces.append(dict(resource=a,x=x,y=y,width=w,height=h))
# Surgical sleeve-strip repair from existing authoritative pose 1 shoulder only.
old=Image.open(H/'chuck-run-2-clean.png').convert('RGBA');new=old.copy();donor=Image.open(R/'assets/running/chuck-0.png').convert('RGBA');changed=[]
for y in range(23,40):
 for x in range(53,66):
  c=old.getpixel((x,y));d=donor.getpixel((x,y))
  # Narrow redundant upright sleeve / exposed-arm remnant, not the outer vest or rear glove.
  if x<=61 and y<=31 or 59<=x<=63 and 27<=y<=37:
   if c!=d:new.putpixel((x,y),d);changed.append([x,y])
new.save(O/'chuck-run-2-final.png');(O/'source/run-strip-changed-pixels.json').write_text(json.dumps(changed)+'\n')
m=json.loads((R/'assets/running/manifest.json').read_text());parts=m['actors'][1]['frames'][2]['parts']
seq=json.loads((R/'assets/attack-sequence/manifest.json').read_text());indexed=quant(new)
for prefix,source,pp,shift in [('RD','RC',parts[:2],0),('DT','CT',seq['frames'][1][6][1:],16)]:
 for k,p in enumerate(pp):
  b=(H/f'{source}{k}.TGA').read_bytes();w,h=struct.unpack_from('<HH',b,12);raw=bytearray(b[786:])
  for x,y in changed:
   tx,ty=x-p['x'],y+shift-p['y']
   if 0<=tx<w and 0<=ty<h:raw[(h-1-ty)*w+tx]=indexed.getpixel((x,y))
  (O/f'{prefix}{k}.TGA').write_bytes(b[:786]+raw)
total=sum(p['bytes'] for p in res);m=dict(parent='99ac5d48ea5e69fdfae7bee00edaeb462d0f8880',resources=res,lowers=pieces,bytes=total,replaced_bytes=6336,boot_bytes=448672-6336+total,free_bytes=458488-448672+6336-total,slots=254-3+len(res),root=[64,92],upper_reuse='Exact PH02 / PH07, translated down 14 native pixels at final collapse',phase_ticks=[8,16,96],palette_banks_added=0)
assert m['free_bytes']>0 and m['slots']<=255;(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
s=['#ifndef MF_PLAYER_DEATH_DATA_H','#define MF_PLAYER_DEATH_DATA_H',f'#define MF_PD_BYTES {total}u','#define MF_PD_NEW 2','#define MF_PD_REPLACED 6336u','static const mf_polish_resource pd_resources[MF_PD_NEW]={']+['{"%s",%d,%d,%du},'%(p['name'],p['width'],p['height'],p['bytes']) for p in res]+['};','static const mf_polish_piece pd_lower[2]={']+['{%d,%d,%d,%d,%d},'%tuple(p[k] for k in ['resource','x','y','width','height']) for p in pieces]+['};','#endif'];(R/'src/player_death_data.h').write_text('\n'.join(s)+'\n');print(json.dumps(m,indent=2))
