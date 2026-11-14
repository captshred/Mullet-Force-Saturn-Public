#!/usr/bin/env python3
"""Review-only native/enlarged crops; never modify source pixels or runtime data."""
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];D=R/'docs/intersection-detail-complete';cur=Image.open(D/'intersection-640.png');before=Image.open(R/'docs/intersection-hotel-detail/intersection-640.png')
for name,box in [('hotel-to-records',(400,0,640,164)),('deli-to-intersection',(190,0,290,164)),('old-strip-transition',(1180,48,1390,170))]:
 im=Image.open(D/'panorama.png') if name=='old-strip-transition' else cur;q=im.crop(box);q.resize((q.width*3,q.height*3),Image.Resampling.NEAREST).save(D/(name+'.png'))
out=Image.new('RGB',(1280,262),(21,27,34));out.paste(before,(0,22));out.paste(cur,(640,22));d=ImageDraw.Draw(out);d.text((5,5),'Approved hotel baseline',fill='white');d.text((645,5),'Complete remaining foreground detail',fill='white');out.save(D/'extension-before-after.png')
old=Image.open(R/'docs/level1-neon-strip-phase2/panorama.png');panels=[('Original mini-mall',old.crop((155,56,275,152))),('Approved hotel (unchanged)',cur.crop((416,40,536,136))),('Residential/DELI',cur.crop((128,40,248,136))),('RECORDS',cur.crop((520,40,640,136)))];out=Image.new('RGB',(740,640),(21,27,34));d=ImageDraw.Draw(out)
for i,(label,im) in enumerate(panels):
 x=i%2*370;y=i//2*320;d.text((x+5,y+5),label,fill='white');out.paste(im.resize((360,288),Image.Resampling.NEAREST),(x+5,y+24))
out.save(D/'detail-quality-comparison.png')
