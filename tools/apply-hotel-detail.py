#!/usr/bin/env python3
"""Map the native hotel study to the unchanged shared palette, hotel mask only.
No overlays: replace the underlying indexed material pixels before packing.
"""
from pathlib import Path
import hashlib,json,struct
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'art/intersection-hotel-detail';O=R/'assets/level1-intersection'
old=(A/'before.bin').read_bytes();im=Image.open(A/'hotel-native-study.png').convert('RGB');assert im.size==(120,152)
pal=[0,*struct.unpack('>255H',(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())];rgb=np.array([[(c>>s)&31 for s in (0,5,10)] for c in pal],np.int32)
source=np.array(im,np.int32)>>3;allowed=np.array([i for i in range(1,256) if not 240<=i<=247]);mapped=allowed[((source[:,:,None,:]-rgb[None,None,allowed,:])**2).sum(axis=-1).argmin(axis=-1)]
new=bytearray(old);mask=bytearray(640*240)
# Retain the original outer rim/threshold where the facade meets other planes.
for y in range(0,151):
 for x in range(418,534):
  at=y*640+x;new[at]=int(mapped[y,x-416]);mask[at]=1
(A/'mask.bin').write_bytes(mask);(O/'EXTPIX.BIN').write_bytes(new)
proof=dict(baseline='8d85905eb12421cfe356b994ebab43893680e1b1',region=[416,0,536,152],editable_inset=[418,0,534,151],outside_changes=sum(a!=b and not m for a,b,m in zip(old,new,mask)),changed_pixels=sum(a!=b for a,b in zip(old,new)),mask_sha256=hashlib.sha256(mask).hexdigest(),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest(),study_sha256=hashlib.sha256((A/'hotel-native-study.png').read_bytes()).hexdigest(),palette_sha256=hashlib.sha256((R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes()).hexdigest(),scope='Hotel front facade and stone arch only; outer plane edges, original side-facing HOTEL neon, records/residential, perspective/road, older1280px and palette unchanged; user review pending')
(A/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
colors=(rgb*255//31).astype(np.uint8);before=Image.fromarray(colors[np.frombuffer(old,np.uint8).reshape(240,640)]);after=Image.fromarray(colors[np.frombuffer(new,np.uint8).reshape(240,640)])
before.save(A/'extension-before.png');after.save(A/'extension-after.png')
from PIL import ImageDraw
canvas=Image.new('RGB',(1000,800),(22,28,35));d=ImageDraw.Draw(canvas)
for col,q in enumerate((before,after)):
 crop=q.crop((416,0,536,152));x=col*500+12;d.text((x,8),('Approved 8d85905','Hotel detail candidate')[col],fill='white');canvas.paste(crop,(x,30));canvas.paste(crop.resize((360,456),Image.Resampling.NEAREST),(x+130,30))
 canvas.paste(q.crop((400,36,552,152)).resize((456,348),Image.Resampling.NEAREST),(col*500+12,444))
canvas.save(R/'docs/intersection-hotel-detail/before-after.png');after.save(R/'docs/intersection-hotel-detail/intersection-after.png')
print(json.dumps(proof,indent=2))
