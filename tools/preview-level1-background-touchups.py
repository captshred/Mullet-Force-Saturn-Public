#!/usr/bin/env python3
"""Native indexed before/after review sheets; nearest-neighbor magnification."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,struct
R=Path(__file__).resolve().parents[1];A=R/'art/level1-background-touchups';O=R/'docs/level1-background-touchups';O.mkdir(parents=True,exist_ok=True)
words=[0]+list(struct.unpack('>255H',(A/'original/CIPAL.BIN').read_bytes()));pal=[tuple(((v>>s)&31)*255//31 for s in (0,5,10)) for v in words]
def image(path):
 im=Image.frombytes('P',(640,240),path.read_bytes());im.putpalette(sum((list(c) for c in pal),[]));return im.convert('RGB')
before=image(A/'original/CIPIX.BIN');after=image(R/'assets/city-cleanup/CIPIX.BIN');before.save(O/'before.png');after.save(O/'after.png')
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
except OSError:font=ImageFont.load_default()
def compare(name,box,scale):
 pair=[im.crop(box) for im in (before,after)];w=pair[0].width*scale;h=pair[0].height*scale;out=Image.new('RGB',(w*2+24,h+36),(27,33,43));d=ImageDraw.Draw(out)
 for i,im in enumerate(pair):d.text((i*(w+24)+5,8),'BEFORE' if i==0 else 'AFTER — REVIEW CANDIDATE',fill='white',font=font);out.paste(im.resize((w,h),Image.Resampling.NEAREST),(i*(w+24),32))
 out.save(O/name)
compare('full-before-after.png',(0,0,640,240),1)
compare('ion-arcade-before-after.png',(392,72,514,104),6)
compare('vinyl-post-before-after.png',(514,55,552,158),6)
compare('mullet-post-before-after.png',(145,55,183,158),6)
regions=after.copy();d=ImageDraw.Draw(regions)
for r in json.loads((A/'provenance.json').read_text())['regions']:
 x0,y0,x1,y1=r['box'];d.rectangle((x0-1,y0-1,x1,y1),outline='#ffffff')
regions.resize((1280,480),Image.Resampling.NEAREST).save(O/'repair-regions.png')
print('Wrote full background, ION ARCADE, VINYL and matching MULLET post comparisons')
