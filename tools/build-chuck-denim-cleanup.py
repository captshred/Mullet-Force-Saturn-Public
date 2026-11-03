#!/usr/bin/env python3
"""Surgical native indexed patches; original approved art stays immutable."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib
R=Path(__file__).resolve().parents[1];O=R/'assets/chuck-denim-cleanup';P=R/'assets/player-death';rm=json.loads((R/'assets/running/manifest.json').read_text());seq=json.loads((R/'assets/attack-sequence/manifest.json').read_text())
donor=Image.open(R/'assets/running/chuck-0.png').convert('RGBA');frames=[];changes={};replacements=[]
for f in range(4):
 path=P/'chuck-run-2-final.png' if f==2 else R/f'assets/running/chuck-{f}.png';old=Image.open(path).convert('RGBA');new=old.copy()
 if f==2:
  for y in range(23,35):
   for x in [51,52]:
    new.putpixel((x,y),donor.getpixel((x,y)) if y<32 else (0,0,0,0))
 if f==3:
  for y in [42,43]:
   for x in range(57,82):new.putpixel((x,y),donor.getpixel((x-2,y+2)))
 changed=[(x,y) for y in range(96) for x in range(128) if old.getpixel((x,y))!=new.getpixel((x,y))];changes[str(f)]=changed;new.save(O/f'chuck-{f}.png');frames.append(new)
 if not changed:continue
 run=rm['actors'][1]['frames'][f]['parts'];prep=seq['frames'][1][f+4];patches=[]
 for k,p in enumerate(run):
  if any(p['x']<=x<p['x']+p['width'] and p['y']<=y<p['y']+p['height'] for x,y in changed):
   name=f'RD{k}.TGA' if f==2 else f'RN{p["resource"]-81:02}.TGA';source=P/name if f==2 else R/'assets/running'/name;patches.append((name,source,p,0))
 for p in prep:
  if any(p['x']<=x<p['x']+p['width'] and p['y']<=y+16<p['y']+p['height'] for x,y in changed):
   name=f'DT{p["resource"]-51}.TGA' if f==2 else seq['resources'][p['resource']]['name'];source=P/name if f==2 else R/'assets/attack-sequence'/name;patches.append(('COMBAT/'+name,source,p,16))
 for dest,source,p,shift in patches:
  b=source.read_bytes();pal=[tuple(b[18+3*i:21+3*i][::-1]) for i in range(256)];lookup={c:i for i,c in reversed(list(enumerate(pal[1:254],start=1)))};w,h=struct.unpack_from('<HH',b,12);raw=bytearray(b[786:])
  for x,y in changed:
   tx,ty=x-p['x'],y+shift-p['y']
   if 0<=tx<w and 0<=ty<h:
    c=new.getpixel((x,y));raw[(h-1-ty)*w+tx]=lookup[c[:3]] if c[3] else 0
  name=dest.split('/')[-1];blob=b[:786]+raw;(O/name).write_bytes(blob);replacements.append(dict(name=name,disc_path=dest,source=str(source.relative_to(R)),frame=f,piece=p,shift=shift,sha256=hashlib.sha256(blob).hexdigest(),source_sha256=hashlib.sha256(b).hexdigest()))
meta=dict(parent='0fbc5fbb6918446368187603b7f3e49d411af93a',changes=changes,replacements=replacements,boot_bytes=446304,free_bytes=12184,slots=253,extra_bytes=0,extra_definitions=0)
(O/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');print({f:len(v) for f,v in changes.items()});print([(p['disc_path'],p['source']) for p in replacements])
