from preserved_source import preserved_bytes
from pathlib import Path
from PIL import Image
import json,hashlib,struct
from player_hurt_previews import hurt,M,O,R,decode

def validate():
 pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];total=0
 for p in M['resources']:
  b=(O/p['name']).read_bytes();w,h=struct.unpack_from('<HH',b,12);assert b[18:786]==pal and max(b[786:])<254 and w%8==h%2==0 and len(b)==786+w*h;assert hashlib.sha256(b).hexdigest()==p['sha256'];total+=(w*h+31)&~31
 for a,n in enumerate(['buck','chuck']):
  for f in range(3):
   expected=Image.open(O/f'{n}-hurt-{f}.png').convert('RGBA');got=hurt(a,f);assert got.getbbox()[3]==92 and got.getchannel('A').tobytes()==expected.getchannel('A').tobytes();assert all(got.getpixel((x,y))==expected.getpixel((x,y)) for y in range(96) for x in range(128) if got.getpixel((x,y))[3])
 changed=set(map(tuple,json.loads((O/'source/run-changed-pixels.json').read_text())));old=Image.open(R/'assets/running/chuck-2.png').convert('RGBA');new=Image.open(O/'chuck-run-2-clean.png').convert('RGBA');assert changed and all(old.getpixel((x,y))==new.getpixel((x,y)) for y in range(96) for x in range(128) if (x,y) not in changed)
 manifest=json.loads((R/'assets/running/manifest.json').read_text());parts=manifest['actors'][1]['frames'][2]['parts'];out=Image.new('RGBA',(128,96))
 for k,p in enumerate(parts):
  file=O/f'RC{k}.TGA' if k<2 else R/'assets/running'/f'RN{p["resource"]-81:02}.TGA';tile=decode(file);out.alpha_composite(tile,(p['x'],p['y']))
  if k<2:
   original=(R/'assets/running'/f'RN{p["resource"]-81:02}.TGA').read_bytes();b=file.read_bytes();assert b[:786]==original[:786]
   for yy in range(p['height']):
    for xx in range(p['width']):
     if (p['x']+xx,p['y']+yy) not in changed:assert b[786+(p['height']-1-yy)*p['width']+xx]==original[786+(p['height']-1-yy)*p['width']+xx]
 assert out.tobytes()==new.tobytes()
 seq=json.loads((R/'assets/attack-sequence/manifest.json').read_text())
 for k,p in enumerate(seq['frames'][1][6][1:]):
  rid=p['resource'];assert [(a,f) for a,frames in enumerate(seq['frames']) for f,parts in enumerate(frames) if any(q['resource']==rid for q in parts)]==[(1,6)]
  old_bytes=(R/'assets/attack-sequence'/seq['resources'][rid]['name']).read_bytes();new_bytes=(O/f'CT{k}.TGA').read_bytes();assert old_bytes[:786]==new_bytes[:786]
  for y in range(p['height']):
   for x in range(p['width']):
    if (p['x']+x,p['y']+y-16) not in changed:assert old_bytes[786+(p['height']-1-y)*p['width']+x]==new_bytes[786+(p['height']-1-y)*p['width']+x]
 lock=json.loads((O/'source/preserved-sha256.json').read_text())
 for n,h in lock.items():assert hashlib.sha256(preserved_bytes(R,n)).hexdigest()==h,n
 hands=json.loads((R/'assets/running-bat-visual/manifest.json').read_text())['hands'][1];assert all(new.getpixel(tuple(p))==old.getpixel(tuple(p)) for p in hands if old.getpixel(tuple(p))[3])
 assert total==M['bytes'] and M['boot_bytes']==422208-5120+total and M['slots']==254 and M['free_bytes']==458488-M['boot_bytes']>0
 print(f"PASS HQ hurt / arm cleanup: ten shared textures; {len(changed)} localized run pixels; exact Buck run/gameplay/audio/enemy/jump assets; {M['boot_bytes']} used, {M['free_bytes']} free, {M['slots']} definitions")
if __name__=='__main__':validate()
