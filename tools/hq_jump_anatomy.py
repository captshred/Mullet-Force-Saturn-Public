#!/usr/bin/env python3
from preserved_source import preserved_bytes
"""Native before/after review and development-only projected joint annotations."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,re
from hq_jump_previews import render
R=Path(__file__).resolve().parents[1];O=R/'assets/hq-jump-anatomy'
JOINTS={
 'buck':{3:[[[56,49],[40,52],[51,70]],[[73,49],[88,52],[78,70]]],4:[[[56,49],[50,66],[40,82]],[[73,49],[84,67],[92,82]]],6:[[[56,49],[45,64],[62,74]],[[73,49],[97,51],[114,52]]]},
 'chuck':{3:[[[56,49],[41,54],[50,71]],[[73,49],[87,54],[77,71]]],4:[[[56,49],[48,66],[38,82]],[[73,49],[85,67],[94,83]]],6:[[[56,49],[42,65],[60,73]],[[73,49],[94,53],[111,54]]]}}
def validate():
 for path,sha in json.loads((O/'preserved-sha256.json').read_text()).items():
  data=preserved_bytes(R,path)
  data=re.sub(rb'^/\* PLAYERDEATH BEGIN \*/\n.*?^/\* PLAYERDEATH END \*/\n',b'',data,flags=re.M|re.S).replace(b'-MF_PD_REMOVED',b'').replace(b'+MF_PD_EXTRA',b'')
  data=re.sub(rb'^/\* PLAYERHURT BEGIN \*/\n.*?^/\* PLAYERHURT END \*/\n',b'',data,flags=re.M|re.S).replace(b'+MF_PH_EXTRA',b'').replace(b'-MF_PH_REMOVED',b'').replace(b'hurt_visible || ',b'')
  data=re.sub(rb'^/\* CPHQ BEGIN \*/\n.*?^/\* CPHQ END \*/\n',b'',data,flags=re.M|re.S)
  if path=='src/animation_preview.c':data=re.sub(rb'^/\* ANATOMY BEGIN \*/\n.*?^/\* ANATOMY END \*/\n',b'',data,flags=re.M|re.S)
  assert hashlib.sha256(data).hexdigest()==sha,path
 for n in ['buck','chuck']:
  a=['buck','chuck'].index(n)
  for k in [0,1,2,5]:assert render(a,k).tobytes()==Image.open(O/'before'/f'{n}-pose-{k}.png').convert('RGBA').tobytes(),(n,k,'approved pose changed')
 for rid in [0,1,5,6]:assert (R/f'assets/hq-jump/HJ{rid:02}.TGA').read_bytes()==(O/f'before/HJ{rid:02}.TGA').read_bytes()
 m=json.loads((R/'assets/hq-jump/manifest.json').read_text());assert m['slots']==254 and m['boot_bytes']<=458488
 print('PASS anatomy refinement: exact guard/takeoff/ascent/landing, original upper/first-lower texture bytes, unchanged phase/physics/audio/other assets; only appended band draw assembly')
 return m

def main():
 validate()
 for a,n in enumerate(['buck','chuck']):
  sheet=Image.new('RGBA',(960,144),(16,20,32,255));d=ImageDraw.Draw(sheet)
  for i,(key,label) in enumerate([(6,'kick'),(3,'tuck'),(4,'descent')]):
   old=Image.open(O/'before'/f'{n}-pose-{key}.png').convert('RGBA');new=render(a,key);pair=Image.new('RGBA',(320,144),(16,20,32,255));pair.alpha_composite(old);pair.alpha_composite(new,(160,0));pd=ImageDraw.Draw(pair);pd.text((3,115),'BEFORE '+label,fill='white');pd.text((163,115),'AFTER '+label,fill='white')
   for z in [1,4]:pair.resize((320*z,144*z),Image.Resampling.NEAREST).save(O/f'{n}-{label}-before-after-{z}x.png')
   sheet.alpha_composite(pair,(i*320,0))
   diag=Image.new('RGBA',(160,152),(16,20,32,255));diag.alpha_composite(new);draw=ImageDraw.Draw(diag)
   for leg,color in zip(JOINTS[n][key],['cyan','yellow']):
    points=[(x,y+16) for x,y in leg];draw.line(points,fill=color,width=1)
    for (x,y),mark in zip(points,['H','K','A']):draw.ellipse((x-1,y-1,x+1,y+1),outline=color);draw.text((x+2,y-4),mark,fill=color)
   draw.line((20,(48 if key==4 else 50)+16,135,(48 if key==4 else 50)+16),fill='orange');draw.ellipse((62,63,66,67),outline='red');draw.text((67,59),'P',fill='red');draw.text((2,115),'H hip  K knee  A ankle',fill='white');draw.text((2,128),'P pelvis / orange seam',fill='orange');draw.text((2,140),'DEV ONLY - '+label,fill='white')
   for z in [1,4]:diag.resize((160*z,152*z),Image.Resampling.NEAREST).save(O/f'{n}-{label}-diagnostic-{z}x.png')
  for z in [1,4]:sheet.resize((960*z,144*z),Image.Resampling.NEAREST).save(O/f'{n}-contact-{z}x.png')
 (O/'joint-annotations.json').write_text(json.dumps(JOINTS,indent=2)+'\n')
if __name__=='__main__':main()
