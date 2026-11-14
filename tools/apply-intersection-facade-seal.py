#!/usr/bin/env python3
"""Repair missing facade material and remove baked sky/moon, without an overlay."""
from pathlib import Path
import numpy as np,struct,json,hashlib,math
R=Path(__file__).resolve().parents[1];A=R/'art/intersection-facade-seal';old=np.frombuffer((A/'before.bin').read_bytes(),np.uint8).reshape(240,640);new=old.copy();mask=np.zeros_like(old)
pal=np.array([0,*struct.unpack('>255H',(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())]);colors=np.stack([(pal>>s)&31 for s in (0,5,10)],-1).astype('int32');allowed=np.array([i for i in range(1,256) if not 240<=i<=247]);dark=allowed[((colors[:,None,:]*np.array([.28,.25,.45])-colors[None,allowed,:])**2).sum(-1).argmin(-1)]
# This upper garage region is a baked city silhouette, not an independent plane.
# Reuse native masonry from the adjoining upper facade; no new palette colors.
for y in range(56):
 for x in range(62):new[y,x]=old[y%28,128+x%24];mask[y,x]=1
# Stay under the existing cornice silhouette; preserve ALL nonzero detail here.
for x in range(241,291):
 estimate=math.ceil(14+(x-241)*.85) if x<279 else math.ceil(47+(x-279)*.65)
 top=min([y for y in range(max(0,estimate-2),min(56,estimate+3)) if old[y,x]!=0] or [estimate])
 for y in range(top,56):
  if old[y,x]==0:new[y,x]=dark[old[y%28,128+x%24]];mask[y,x]=2
for x in range(337,416):
 estimate=max(0,math.ceil(31-(x-366)*.82))
 top=min([y for y in range(max(0,estimate-2),min(56,estimate+3)) if old[y,x]!=0] or [estimate])
 for y in range(top,56):
  if old[y,x]==0:new[y,x]=dark[old[y%28,128+x%24]];mask[y,x]=2
# Orange crescent and its antialias pixels exist only in this isolated source box.
for y in range(27,41):
 for x in range(324,338):
  if old[y,x]!=0:new[y,x]=0;mask[y,x]=3
(R/'assets/level1-intersection/EXTPIX.BIN').write_bytes(new.tobytes());(A/'mask.bin').write_bytes(mask.tobytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
proof=dict(baseline='5363539d048062af7e862d75dd232db4bb310aad',before_sha256=sha(old.tobytes()),after_sha256=sha(new.tobytes()),mask_sha256=sha(mask.tobytes()),changed_pixels=int((new!=old).sum()),regions={str(v):int((mask==v).sum()) for v in (1,2,3)},side_nonzero_changes=int(((new!=old)&(mask==2)&(old!=0)).sum()))
(A/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
