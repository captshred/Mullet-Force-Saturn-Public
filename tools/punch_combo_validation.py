#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,hashlib,struct
R=Path(__file__).resolve().parents[1]
def validate(root=R,files=None):
 o=root/'assets/punch-combo';m=json.loads((o/'manifest.json').read_text());pal=(root/m['palette']).read_bytes()[18:786]
 assert hashlib.sha256(pal).hexdigest()==m['palette_sha256']
 assert hashlib.sha256((o/'source/rear-cross-study.png').read_bytes()).hexdigest()==m['source_sha256']
 from jab_cohesion_previews import decode
 for a,p in enumerate(m['resources']):
  b=(o/p['name']).read_bytes();w,h=struct.unpack_from('<HH',b,12);assert (w,h)==(80,44) and b[18:786]==pal and b[16:18]==b'\x08\0' and len(b)==786+w*h and max(b[786:])<254
  assert hashlib.sha256(b).hexdigest()==p['sha256'] and p['bytes']==(w*h+31)&~31
  im=decode(o/p['name']);assert im.tobytes()==Image.open(o/f'{p["actor"]}-upper-native.png').convert('RGBA').tobytes()
  assert list(im.getbbox())==p['opaque_bounds'] and set(im.getchannel('A').getdata())=={0,255}
  if files is not None:assert files['COMBO/'+p['name']]==b
 assert m['added_bytes']==7040 and m['boot_bytes']==446304+7040 and m['free_bytes']==458488-m['boot_bytes']==5144 and m['definitions']==255 and m['added_definitions']==2
 print('PASS combo: two80x44 textures,unchanged shared palette,raw0 transparency,2 registrations,+7040 bytes;453344 allocated,5144 free,255 definitions;approved head/grounded lower reuse')
 return m
if __name__=='__main__':validate()
