from preserved_source import preserved_bytes
from pathlib import Path
from PIL import Image
import json,struct,hashlib,re,subprocess
from player_death_previews import R,O,M,render,decode

def validate():
 for n,h in json.loads((O/'source/preserved-sha256.json').read_text()).items():assert hashlib.sha256(preserved_bytes(R,n)).hexdigest()==h,n
 pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];total=0
 for p in M['resources']:
  b=(O/p['name']).read_bytes();w,h=struct.unpack_from('<HH',b,12);assert b[:3]==b'\0\1\1' and b[18:786]==pal and len(b)==786+w*h and w%8==h%2==0 and max(b[786:])<254;assert hashlib.sha256(b).hexdigest()==p['sha256'];total+=(w*h+31)&~31
 for a,n in enumerate(['buck','chuck']):
  source=Image.open(O/f'{n}-collapse.png').convert('RGBA');got=render(a,2);assert got.getbbox()[3]==92
  assert got.getchannel('A').tobytes()==source.getchannel('A').tobytes()
  assert all(got.getpixel((x,y))==source.getpixel((x,y)) for y in range(96) for x in range(128) if got.getpixel((x,y))[3])
  upper=Image.open(R/f'assets/player-hurt/{n}-hurt-2.png').convert('RGBA').crop((0,0,128,52));crop=got.crop((0,14,128,66));assert crop.getchannel('A').tobytes()==upper.getchannel('A').tobytes();assert all(crop.getpixel((x,y))==upper.getpixel((x,y)) for y in range(52) for x in range(128) if upper.getpixel((x,y))[3])
 old=Image.open(R/'assets/player-hurt/chuck-run-2-clean.png').convert('RGBA');new=Image.open(O/'chuck-run-2-final.png').convert('RGBA');changed=set(map(tuple,json.loads((O/'source/run-strip-changed-pixels.json').read_text())));assert changed and all(53<=x<=65 and 23<=y<=39 for x,y in changed)
 assert all(new.getpixel((x,y))==old.getpixel((x,y)) for y in range(96) for x in range(128) if (x,y) not in changed)
 hands=json.loads((R/'assets/running-bat-visual/manifest.json').read_text())['hands'][1]
 for p in hands:assert old.getpixel(tuple(p))==new.getpixel(tuple(p))
 rm=json.loads((R/'assets/running/manifest.json').read_text());seq=json.loads((R/'assets/attack-sequence/manifest.json').read_text())
 for dst,src,parts,shift in [('RD','RC',rm['actors'][1]['frames'][2]['parts'][:2],0),('DT','CT',seq['frames'][1][6][1:],16)]:
  for k,p in enumerate(parts):
   original=(R/f'assets/player-hurt/{src}{k}.TGA').read_bytes();b=(O/f'{dst}{k}.TGA').read_bytes();assert b[:786]==original[:786];w,h=struct.unpack_from('<HH',b,12)
   for yy in range(h):
    for xx in range(w):
     if (p['x']+xx,p['y']+yy-shift) not in changed:assert b[786+(h-1-yy)*w+xx]==original[786+(h-1-yy)*w+xx]
 out=Image.new('RGBA',(128,96))
 for k,p in enumerate(rm['actors'][1]['frames'][2]['parts']):out.alpha_composite(decode(O/f'RD{k}.TGA' if k<2 else R/f'assets/running/RN{p["resource"]-81:02}.TGA'),(p['x'],p['y']))
 assert out.tobytes()==new.tobytes()
 # Existing animation source is byte-identical once the explicit optional presentation blocks are removed.
 for name in ['src/main.c','src/animation_preview.c','src/animation_preview.h']:
  s=preserved_bytes(R,name);s=re.sub(rb'^/\* PLAYERDEATH BEGIN \*/\n.*?^/\* PLAYERDEATH END \*/\n',b'',s,flags=re.M|re.S).replace(b'-MF_PD_REMOVED',b'').replace(b'+MF_PD_EXTRA',b'');baseline=json.loads((O/'source/presentation-baseline-sha256.json').read_text());assert hashlib.sha256(s).hexdigest()==baseline[name],name
 assert total==M['bytes']==3968 and M['boot_bytes']==446304 and M['slots']==253 and M['free_bytes']==12184
 print(f"PASS HQ death: exact approved hurt/Buck run/gameplay/audio; two shared new lowers, exact upper reuse; {len(changed)} Chuck shoulder pixels; {M['boot_bytes']} bytes, {M['free_bytes']} free, {M['slots']} definitions")
if __name__=='__main__':validate()
