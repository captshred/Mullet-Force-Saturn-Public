#!/usr/bin/env python3
from preserved_source import preserved_bytes
"""Reconstruct byte-identical normal/mirrored native frames from Saturn pieces."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib
R=Path(__file__).resolve().parents[1]
def validate_running(root=R,files=None):
 o=root/'assets/running';m=json.loads((o/'manifest.json').read_text());assert hashlib.sha256((o/'source/run-sheet.png').read_bytes()).hexdigest()==m['source_sha256'];pal=(root/m['palette']).read_bytes()[18:786];colors=[tuple(pal[3*i:3*i+3][::-1]) for i in range(256)];total=0;seen=set()
 for r in m['resources']:
  blob=(o/r['name']).read_bytes();w,h=struct.unpack_from('<HH',blob,12)
  assert blob[:3]==b'\0\1\1' and blob[16:18]==b'\x08\0' and blob[18:786]==pal and w%8==0 and h%2==0
  assert (w,h)==(r['width'],r['height']) and len(blob)==786+w*h and max(blob[786:])<254
  assert hashlib.sha256(blob).hexdigest()==r['sha256'];key=(w,h,blob[786:]);assert key not in seen;seen.add(key);total+=(w*h+31)&~31
  if files is not None:assert files[r['name']]==blob
 existing=set()
 for folder in ['gallery','animation-study','animation-polish']:
  for path in (root/'assets'/folder).glob('*.TGA'):
   blob=path.read_bytes()
   if blob[18:786]==pal:
    w,h=struct.unpack_from('<HH',blob,12);existing.add((w,h,blob[786:]))
 assert not (seen & existing),'New piece duplicates an existing resource'
 for a in m['actors']:
  hashes=[]
  for f in a['frames']:
   im=Image.new('RGBA',(128,96));occupied=set()
   for p in f['parts']:
    r=m['resources'][p['resource']-81];blob=(o/r['name']).read_bytes();w,h=r['width'],r['height'];raw=blob[786:];tile=Image.new('RGBA',(w,h));tile.putdata([(*colors[i],255) if i else (0,0,0,0) for y in range(h) for i in raw[(h-1-y)*w:(h-y)*w]])
    for y in range(h):
     for x in range(w):
      if tile.getpixel((x,y))[3]:assert (p['x']+x,p['y']+y) not in occupied;occupied.add((p['x']+x,p['y']+y))
    im.alpha_composite(tile,(p['x'],p['y']))
   src=Image.open(o/f"{a['name']}-{f['frame']}.png").convert('RGBA');assert im.tobytes()==src.tobytes();digest=hashlib.sha256(src.tobytes()).hexdigest();assert digest==f['sha256'];hashes.append(digest)
   # Reflect whole composed frame and independently reflect each piece/root.
   mirror=Image.new('RGBA',(128,96))
   for p in f['parts']:
    tile=im.crop((p['x'],p['y'],p['x']+p['width'],p['y']+p['height'])).transpose(Image.Transpose.FLIP_LEFT_RIGHT);mirror.alpha_composite(tile,(128-p['x']-p['width'],p['y']))
   assert mirror.tobytes()==src.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
   if f['frame'] in (0,2):assert src.getbbox()[3]==92
  assert len(set(hashes))==4 and hashes[0]!=hashes[2] and hashes[1]!=hashes[3]
 assert total==m['texture_bytes'] and m['boot_vdp1_bytes']==362848+total and m['free_vdp1_bytes']==458488-m['boot_vdp1_bytes'] and m['free_vdp1_bytes']>0
 locked=json.loads((o/'approved-sha256.json').read_text())
 for name,digest in locked.items():assert hashlib.sha256(preserved_bytes(root,name)).hexdigest()==digest,name
 print(f"PASS running: eight distinct native poses, exact3-piece reconstruction/mirroring, shared palette/binary alpha,24 resources/{total} bytes; approved assets unchanged")
 if "stride_correction" in m:
  from stride_validation import validate_stride
  validate_stride(root)
 if "artifact_correction" in m:
  from leg_artifact_validation import validate_leg_artifacts
  validate_leg_artifacts(root)
 return m
if __name__=='__main__':validate_running()
