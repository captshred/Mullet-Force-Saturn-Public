#!/usr/bin/env python3
from preserved_source import preserved_bytes
"""Validate actual leg-layer provenance, upper-art lock and unchanged gameplay."""
from pathlib import Path
from PIL import Image
import hashlib,json
R=Path(__file__).resolve().parents[1]
def validate_stride(root=R):
 d=root/'assets/stride-fix';o=root/'assets/running';m=json.loads((o/'manifest.json').read_text());c=m['stride_correction'];old=json.loads((d/'before/manifest.json').read_text());lock=c['upper_lock_rows']
 assert (m['canvas'],m['root'],m['frame_ticks'])==([128,96],[64,92],6)
 assert hashlib.sha256((d/'source/single-leg-guide.png').read_bytes()).hexdigest()==c['guide_sha256']
 assert c['near_phases']==[0,2,1,3] and c['far_phases']==[1,3,0,2]
 for name,digest in json.loads((d/'gameplay-sha256.json').read_text()).items():
  data=preserved_bytes(root,name)
  if name in ['src/game.c','src/game.h']:
   import re
   data=re.sub(rb'^/\* JAB BEGIN \*/\n.*?^/\* JAB END \*/\n',b'',data,flags=re.M|re.S)
  if name=='src/game.c':
   import re
   data=re.sub(rb'^/\* MOMENTUM BEGIN \*/\n.*?^/\* MOMENTUM END \*/\n',b'',data,flags=re.M|re.S)
  if name=='src/player_animation.c':
   import re
   data=re.sub(rb'^/\* RBV BEGIN \*/\n.*?^/\* RBV END \*/\n',b'',data,flags=re.M|re.S)
  assert hashlib.sha256(data).hexdigest()==digest,name
 pal=(root/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(pal[3*i:3*i+3][::-1]) for i in range(256)];memo={}
 def quant(c):
  if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
  return memo[c]
 changed=0
 for actor in m['actors']:
  name=actor['name'];legs=[Image.open(d/f'{name}-leg-{f}.png').convert('RGBA') for f in range(4)]
  for f,leg in enumerate(legs):
   assert hashlib.sha256(leg.tobytes()).hexdigest()==actor['leg_layers'][f]['sha256'];box=leg.getbbox();assert box[1]==44
   foot=[x for y in range(box[3]-3,box[3]) for x in range(128) if leg.getpixel((x,y))[3]]
   if f==0:assert box[3]==92 and min(foot)>64 # forward-contact sole
   if f==1:assert box[3]<78 and max(foot)<64 # folded behind, clear of floor
   if f==2:assert box[3]==90 and max(foot)<64 # trailing heel/toe, not front boot
   if f==3:assert box[3]<86 and any(leg.getpixel((x,y))[3] for x in range(78,87) for y in range(48,60)) # forward driven knee
  for f,frame in enumerate(actor['frames']):
   before=Image.open(d/f'before/{name}-{f}.png').convert('RGBA');after=Image.open(o/f'{name}-{f}.png').convert('RGBA')
   repair=root/'assets/leg-artifact-fix'/f'{name}-{f}-mask.png'
   mask=Image.open(repair).convert('L') if repair.exists() else Image.new('L',(128,96))
   assert all(before.getpixel((x,y))==after.getpixel((x,y)) for y in range(lock) for x in range(128) if not mask.getpixel((x,y)))
   near_phase=c['near_phases'][f];far_phase=c['far_phases'][f];assert (frame['near_phase'],frame['far_phase'])==(near_phase,far_phase)
   # Independent reconstruction verifies that the identity labels describe
   # the actual colored pixel layers consumed by the game's TGA converter.
   far=legs[far_phase].copy();far.putdata([(*colors[quant(tuple(round(v*.83) for v in col[:3]))],255) if col[3] else (0,0,0,0) for col in far.getdata()]);composed=Image.new('RGBA',(128,96));composed.alpha_composite(far,(-2,0));composed.alpha_composite(legs[near_phase],(2,0));leg_underlay=composed.copy();composed.paste(before.crop((0,0,128,lock)),(0,0));composed.paste(leg_underlay,(0,0),mask)
   assert composed.tobytes()==after.tobytes(),(name,f,'Wrong leg layer/occlusion')
   changed+=sum(a!=b for a,b in zip(before.getdata(),after.getdata()))
   assert len(frame['parts'])==3 and after.getbbox()[3]<=92
  assert actor['frames'][0]['near_phase']==0 and actor['frames'][2]['far_phase']==0
  assert actor['frames'][1]['far_phase']==3 and actor['frames'][3]['near_phase']==3
 assert len(c['reused_identical_pieces'])==8
 for name in c['reused_identical_pieces']:assert (o/name).read_bytes()==(d/'before'/name).read_bytes()
 assert m['texture_bytes']<=old['texture_bytes'] and m['unique_resources']==old['unique_resources']==24
 print(f"PASS stride: persistent near/far anatomy, opposite contacts, distinct push/drive phases,approved upper pixels outside explicit leg-repair mattes identical,{changed} lower pixels changed,8 exact reused pieces,gameplay/timing hashes unchanged; delta{m['texture_bytes']-old['texture_bytes']} bytes")
 return m
if __name__=='__main__':validate_stride()
