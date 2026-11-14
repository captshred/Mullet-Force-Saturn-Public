#!/usr/bin/env python3
"""Replace only index-zero pixels inside explicitly reviewed window openings."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];A=R/'art/intersection-window-opacity'
spec=json.loads((A/'openings.json').read_text());old=(A/'before.bin').read_bytes();new=bytearray(old);mask=bytearray(len(old));counts={}
for opening in spec['openings']:
 x0,y0,x1,y1=opening['box'];count=0
 for y in range(y0,y1):
  for x in range(x0,x1):
   i=y*640+x
   if old[i]==0:mask[i]=1;new[i]=spec['opaque_index'];count+=1
 counts[opening['name']]=count
assert spec['opaque_index'] and len(old)==640*240
(R/'assets/level1-intersection/EXTPIX.BIN').write_bytes(new);(A/'mask.bin').write_bytes(mask)
sha=lambda b:hashlib.sha256(b).hexdigest()
(A/'proof.json').write_text(json.dumps(dict(baseline=spec['baseline'],before_sha256=sha(old),after_sha256=sha(new),mask_sha256=sha(mask),changed_pixels=sum(mask),opaque_index=spec['opaque_index'],opening_changed_pixels=counts),indent=2)+'\n')
print('Window opacity: replaced',sum(mask),'transparent pixels; all existing nonzero pixels preserved')
