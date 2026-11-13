#!/usr/bin/env python3
"""Native indexed before/after review sheets; nearest-neighbor magnification."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,struct
R=Path(__file__).resolve().parents[1];A=R/'art/level1-background-touchups';O=R/'docs/level1-background-touchups';O.mkdir(parents=True,exist_ok=True)
words=[0]+list(struct.unpack('>255H',(A/'original/CIPAL.BIN').read_bytes()));pal=[tuple(((v>>s)&31)*255//31 for s in (0,5,10)) for v in words]
def image(path):
 im=Image.frombytes('P',(640,240),path.read_bytes());im.putpalette(sum((list(c) for c in pal),[]));return im.convert('RGB')
before=image(A/'pole-correction-before.bin');after=image(R/'assets/city-cleanup/CIPIX.BIN');before.save(O/'before.png');after.save(O/'after.png')
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
except OSError:font=ImageFont.load_default()
def compare(name,box,scale):
 pair=[im.crop(box) for im in (before,after)];w=pair[0].width*scale;h=pair[0].height*scale;out=Image.new('RGB',(w*2+24,h+36),(27,33,43));d=ImageDraw.Draw(out)
 for i,im in enumerate(pair):
  label=('BEFORE: previous cleanup' if i==0 else 'AFTER: LEFT pole restored') if 'post' in name else ('BEFORE' if i==0 else 'AFTER — REVIEW CANDIDATE')
  d.text((i*(w+24)+5,8),label,fill='white',font=font);out.paste(im.resize((w,h),Image.Resampling.NEAREST),(i*(w+24),32))
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
# Actual production-renderer captures of both complete lamp assemblies, with
# identical controller schedules on e23b9bc and the corrected source. No painting.
before_report=json.loads((A/'native-before-report.json').read_text())
after_report=json.loads((O/'native-report.json').read_text())
for name,box,frame,oldname,newname in [
 ('native-mullet-lamp-before-after.png',(145,55,183,160),1100,'native-before-left.png','native-left-view.png'),
 ('native-vinyl-lamp-before-after.png',(514,55,552,160),1320,'native-before-vinyl.png','native-ion-vinyl-view.png')]:
 crops=[]
 for path,report in [(A/oldname,before_report),(O/newname,after_report)]:
  camera=next(r['camera'] for r in report['captures'] if r['frame']==frame)
  x0,y0,x1,y1=box;crop=(x0-camera+1,y0+1,x1-camera+1,y1+1)
  im=Image.open(path).convert('RGB');assert 0<=crop[0]<crop[2]<=im.width and crop[3]<=im.height
  crops.append(im.crop(crop))
 w,h=crops[0].width*6,crops[0].height*6;out=Image.new('RGB',(w*2+24,h+36),(27,33,43));d=ImageDraw.Draw(out)
 for i,im in enumerate(crops):
  d.text((i*(w+24)+4,8),'BEFORE: e23b9bc' if not i else 'AFTER: left kept, right gone',fill='white',font=font)
  out.paste(im.resize((w,h),Image.Resampling.NEAREST),(i*(w+24),32))
 out.save(O/name)
