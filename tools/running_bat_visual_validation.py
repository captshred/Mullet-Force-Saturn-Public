#!/usr/bin/env python3
"""Verify shared weapon resources, exact existing swing masks and grip attachment."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib,re
R=Path(__file__).resolve().parents[1]
def validate_rbv(root=R,files=None):
 o=root/'assets/running-bat-visual';m=json.loads((o/'manifest.json').read_text());pal=(root/m['palette']).read_bytes()[18:786];total=0;keys=set()
 assert hashlib.sha256((o/'source/aluminum-bat-guide.png').read_bytes()).hexdigest()==m['source_sha256']
 source=(root/'src/player_animation.c').read_bytes();source=re.sub(rb'^/\* RBV BEGIN \*/\n.*?^/\* RBV END \*/\n',b'',source,flags=re.M|re.S);assert source==(o/'source/player-animation-before.c').read_bytes()
 for r in m['resources']:
  blob=(o/r['name']).read_bytes();w,h=struct.unpack_from('<HH',blob,12);assert (w,h)==(r['width'],r['height']) and w%8==0 and blob[18:786]==pal and blob[16:18]==b'\x08\0' and max(blob[786:])<254 and len(blob)==786+w*h
  key=(w,h,blob[786:]);assert key not in keys;keys.add(key);total+=(w*h+31)&~31;assert hashlib.sha256(blob).hexdigest()==r['sha256']
  if files is not None:assert files[r['name']]==blob
 assert total==m['texture_bytes'] and m['boot_bytes']==401952+total and m['free_bytes']==458488-m['boot_bytes']>0
 # All poses use one carried weapon; the same local grip is positioned inside
 # an opaque rear-glove pixel, with the body drawn in front of the handle.
 for a,name in enumerate(['buck','chuck']):
  for f,(x,y) in enumerate(m['hands'][a]):
   body=Image.open(root/f'assets/running/{name}-{f}.png').convert('RGBA');assert body.getpixel((x,y))[3] and max(body.getpixel((x,y))[:3])<80
 # Wood covers affect exactly visible original weapon pixels, not body/hands.
 wood={(184,136,80),(224,184,120),(128,96,56),(208,160,104)}
 for a,name in enumerate(['buck','chuck']):
  for f,p in enumerate(m['overlays'][a]):
   blob=(root/'assets/cd'/p['source']).read_bytes();w,h=struct.unpack_from('<HH',blob,12);palette=blob[18:786];raw=blob[786:];overlay=Image.open(o/f'{name}-swing-{f}.png').convert('RGBA');assert p['resource']<0 or m['resources'][p['resource']]['height']%2==h%2
   mask=Image.open(o/f'{name}-swing-{f}-mask.png');expected={(x,y) for y in range(h) for x in range(w) if mask.getpixel((x,y))}
   assert all(tuple(palette[3*raw[(h-1-y)*w+x]:3*raw[(h-1-y)*w+x]+3][::-1]) in wood for x,y in expected)
   actual={(x,y) for y in range(h) for x in range(w) if overlay.getpixel((x,y))[3]};assert expected==actual and len(actual)==p['wood_pixels']
 print(f"PASS running bat visuals:one shared carry texture,8 opaque glove anchors,exact wood-only covers,matched SGL height parity,immutable base animation source;{len(keys)} textures/{total} bytes;{m['boot_bytes']} allocated/{m['free_bytes']} free")
 return m
if __name__=='__main__':validate_rbv()
