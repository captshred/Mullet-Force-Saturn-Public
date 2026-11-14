#!/usr/bin/env python3
"""Replace remaining foreground materials only; freeze hotel and all other planes."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,struct
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'art/intersection-detail-complete';O=R/'assets/level1-intersection';D=R/'docs/intersection-detail-complete';D.mkdir(exist_ok=True)
old=(A/'before.bin').read_bytes();new=bytearray(old);mask=bytearray(len(old));pal=[0,*struct.unpack('>255H',(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())];colors=np.array([[(c>>s)&31 for s in (0,5,10)] for c in pal],np.int32);allowed=np.array([i for i in range(1,256) if not 240<=i<=247])
for name,x0,x1 in [('residential',0,241),('records',536,640)]:
 im=Image.open(A/(name+'-native.png')).convert('RGB');assert im.size==(x1-x0,152);rgb=np.array(im,np.int32)>>3
 data=allowed[((rgb[:,:,None,:]-colors[None,None,allowed,:])**2).sum(axis=-1).argmin(axis=-1)]
 for y in range(151):
  for x in range(x0,x1):
   edit=(2<=x<240 and not(y<56 and x<64)) if name=='residential' else x>=538
   if edit:new[y*640+x]=int(data[y,x-x0]);mask[y*640+x]=1
(O/'EXTPIX.BIN').write_bytes(new);(A/'mask.bin').write_bytes(mask)
proof=dict(baseline='89b0332de1bd2c4e84e9f086cd0e078169bd8103',before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest(),mask_sha256=hashlib.sha256(mask).hexdigest(),changed_pixels=sum(a!=b for a,b in zip(old,new)),outside_mask_changes=sum(a!=b and not m for a,b,m in zip(old,new,mask)),hotel_changes=sum(old[y*640+x]!=new[y*640+x] for y in range(152) for x in range(416,536)),scope='All remaining coarse foreground residential/DELI/shutter/RECORDS surfaces; exact hotel, outer plane edges, original1280, road/perspective/sky/lamps/crosswalk/palette frozen; candidate pending user review',source_sha256={n:hashlib.sha256((A/n).read_bytes()).hexdigest() for n in ('residential-native.png','records-native.png')})
(A/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
rgb=(colors*255//31).astype(np.uint8);before=Image.fromarray(rgb[np.frombuffer(old,np.uint8).reshape(240,640)]);after=Image.fromarray(rgb[np.frombuffer(new,np.uint8).reshape(240,640)])
for name,box in [('records',(536,0,640,152)),('residential',(0,0,241,152))]:
 w=box[2]-box[0];canvas=Image.new('RGB',(w*6+32,152*3+36),(21,27,34));draw=ImageDraw.Draw(canvas)
 for col,im in enumerate((before,after)):
  x=col*(w*3+16);draw.text((x+4,5),('Approved hotel baseline','Complete detail candidate')[col],fill='white');canvas.paste(im.crop(box).resize((w*3,456),Image.Resampling.NEAREST),(x,24))
 canvas.save(D/(name+'-before-after.png'))
print(json.dumps(proof,indent=2))
