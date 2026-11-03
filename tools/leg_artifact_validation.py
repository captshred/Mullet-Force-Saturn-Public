#!/usr/bin/env python3
"""Reject the stale upper-leg overlay without permitting wider sprite changes."""
from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1]
def validate_leg_artifacts(root=R):
 d=root/'assets/leg-artifact-fix';o=root/'assets/running';m=json.loads((o/'manifest.json').read_text());old=json.loads((d/'before/manifest.json').read_text());c=m['artifact_correction'];counts=json.loads((d/'changed-pixels.json').read_text());total=0
 assert c['parent']=='aae373fb6fe1b7d0ca63210a071a8bb85ad500c8'
 assert hashlib.sha256((d/'source/cleanup-reference.png').read_bytes()).hexdigest()==c['reference_sha256']
 for path,digest in c['masks'].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest
 assert (m['root'],m['canvas'],m['frame_ticks'])==(old['root'],old['canvas'],old['frame_ticks'])
 for a,actor in enumerate(m['actors']):
  name=actor['name'];assert actor['leg_layers']==old['actors'][a]['leg_layers'],'Actual leg chains were changed'
  for f,frame in enumerate(actor['frames']):
   before=Image.open(d/f'before/{name}-{f}.png').convert('RGBA');after=Image.open(o/f'{name}-{f}.png').convert('RGBA')
   assert hashlib.sha256(before.tobytes()).hexdigest()==old['actors'][a]['frames'][f]['sha256']
   assert (frame['near_phase'],frame['far_phase'])==(old['actors'][a]['frames'][f]['near_phase'],old['actors'][a]['frames'][f]['far_phase'])
   if f in [0,2]:assert before.tobytes()==after.tobytes();continue
   mask=Image.open(d/f'{name}-{f}-mask.png').convert('L');changed=[]
   for y in range(96):
    for x in range(128):
     if before.getpixel((x,y))!=after.getpixel((x,y)):
      assert mask.getpixel((x,y)) and 54<=x<90 and 43<=y<48;changed.append((x,y))
   assert len(changed)==counts[f'{name}-{f}'] and changed
   assert before.crop((0,0,128,43)).tobytes()==after.crop((0,0,128,43)).tobytes()
   assert before.crop((0,48,128,96)).tobytes()==after.crop((0,48,128,96)).tobytes()
   # Known ghost kneecap pixels above the two approved leg chains must clear.
   marker=(81,47) if name=='buck' else ((79,47) if f==1 else (83,47))
   assert before.getpixel(marker)[3] and after.getpixel(marker)[3]==0,(name,f,'Stale kneecap survived')
   total+=len(changed)
 assert total==486 and m['texture_bytes']==old['texture_bytes']==39104
 print('PASS leg artifact repair:486 localized pixels,frames1/3 identical,heads/upper art and all pixels below row47 identical,leg identities/timing/root preserved,stale kneecap regression markers clear')
 return total
if __name__=='__main__':validate_leg_artifacts()
