#!/usr/bin/env python3
"""Repair the baked waist join; no anchor, root, pose or texture dimension changes."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib
R=Path(__file__).resolve().parents[1];O=R/'assets/run-waist-seam';D=R/'assets/chuck-denim-cleanup';RM=json.loads((R/'assets/running/manifest.json').read_text());SEQ=json.loads((R/'assets/attack-sequence/manifest.json').read_text());DM=json.loads((D/'manifest.json').read_text())
meta=dict(parent='3f26c763306e3f231fbaf52870fe9b6a301134dc',frames=[],replacements=[],boot_bytes=446304,free_bytes=12184,slots=253,extra_bytes=0,extra_definitions=0,source_join_y=44,root=[64,92])
def current(path):
 hit=next((p for p in DM['replacements'] if p['disc_path']==path),None)
 if hit:return D/hit['name']
 return R/('assets/attack-sequence' if path.startswith('COMBAT/') else 'assets/running')/path.split('/')[-1]
for a,n in enumerate(['buck','chuck']):
 for f in range(4):
  path=R/f'assets/running/{n}-{f}.png' if a==0 else D/f'chuck-{f}.png';old=Image.open(path).convert('RGBA');new=old.copy()
  if f in [1,3]:
   if a==0:
    belt=43 if f==1 else 42
    for x in range(62,74):
     c=old.getpixel((x,belt));donor=old.getpixel((x,38))
     if c[3] and donor[3] and c[2]>c[0]*1.2:new.putpixel((x,belt),donor)
    rows=[44] if f==1 else [43,44]
   else:
    if f==1:
     for x in range(62,73):
      c=old.getpixel((x,43));donor=old.getpixel((x,38))
      if c[3] and donor[3] and c[2]>c[0]*1.2:new.putpixel((x,43),donor)
    rows=[44]
   for y in rows:
    for x in range(57,74):
     c=old.getpixel((x,y));donor=old.getpixel((x,46))
     if c[3] and donor[3]:new.putpixel((x,y),donor)
   # Buck's fourth pose has a five-pixel cap beyond its trouser/waist contour.
   if a==0 and f==3:
    for x in range(74,79):new.putpixel((x,42),(0,0,0,0))
  changed=[(x,y) for y in range(96) for x in range(128) if old.getpixel((x,y))!=new.getpixel((x,y))];new.save(O/f'{n}-{f}.png');meta['frames'].append(dict(actor=a,frame=f,source=str(path.relative_to(R)),changed=changed,sha256=hashlib.sha256(new.tobytes()).hexdigest()))
  if not changed:continue
  for parts,shift in [(RM['actors'][a]['frames'][f]['parts'],0),(SEQ['frames'][a][f+4],16)]:
   for p in parts:
    if not any(p['x']<=x<p['x']+p['width'] and p['y']<=y+shift<p['y']+p['height'] for x,y in changed):continue
    dest='COMBAT/'+SEQ['resources'][p['resource']]['name'] if shift else f'RN{p["resource"]-81:02}.TGA';source=current(dest);blob=source.read_bytes();w,h=struct.unpack_from('<HH',blob,12);raw=bytearray(blob[786:]);pal=[tuple(blob[18+3*i:21+3*i][::-1]) for i in range(256)];lookup={c:i for i,c in reversed(list(enumerate(pal[1:254],start=1)))}
    for x,y in changed:
     tx,ty=x-p['x'],y+shift-p['y']
     if 0<=tx<w and 0<=ty<h:
      c=new.getpixel((x,y));raw[(h-1-ty)*w+tx]=lookup[c[:3]] if c[3] else 0
    name=dest.split('/')[-1];out=blob[:786]+raw;(O/name).write_bytes(out);meta['replacements'].append(dict(name=name,disc_path=dest,source=str(source.relative_to(R)),actor=a,frame=f,piece=p,shift=shift,sha256=hashlib.sha256(out).hexdigest(),source_sha256=hashlib.sha256(blob).hexdigest()))
(O/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');print([(p['actor'],p['frame'],len(p['changed'])) for p in meta['frames']]);print([p['disc_path'] for p in meta['replacements']])
