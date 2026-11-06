#!/usr/bin/env python3
"""Exact approved-parent scope, native rooftop placement and Saturn budgets."""
from pathlib import Path
import hashlib,json,re,struct
from PIL import Image,ImageDraw
from level2_turret_scope import turret_lock
R=Path(__file__).resolve().parents[1];lock=turret_lock()
assert lock['base_commit']=='812ecb6a8a22bc0de8ab698e6da4e8158a4d803e'
for group in ['frozen','changes','added']:
 for n,e in lock[group].items():
  if group=='changes':e=e['after']
  b=(R/n).read_bytes();assert {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}==e,n
for e in lock['preserved_sections']:
 s=(R/e['file']).read_text();a=s.index(e['begin']);b=s.index(e['end'],a)
 assert hashlib.sha256(s[a:b].encode()).hexdigest()==e['sha256'],(e['file'],e['begin'])
for n in ['src/game.c','src/main.c','src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_audio_data.h','src/chrome_eye_data.h','.github/workflows/build.yml','docs/level2-enemy-lock.json']:
 assert n in lock['frozen'],n
m=json.loads((R/'assets/wingsuit/manifest.json').read_text())
assert all('assets/wingsuit/'+n in lock['frozen'] for n in m['files'])
assert (m['textures'],m['vdp1_bytes'],m['max_sprite_commands'])==(28,33792,81)
assert 33792<458488 and 28<255 and 81<1761
assert m['vdp2_payload_bytes']==65792 and m['cram_bytes']==32
# Decode the real raised plane, never regenerate or edit approved artwork.
chars=(R/'assets/wingsuit/WROOF.BIN').read_bytes();words=struct.unpack('>4096H',(R/'assets/wingsuit/WRMAP.BIN').read_bytes())
roof=Image.new('L',(512,512))
for ty in range(64):
 for tx in range(64):
  tile=((words[ty*64+tx]&4095)-65536//32)//2
  roof.paste(Image.frombytes('L',(8,8),chars[tile*64:tile*64+64]),(tx*8,ty*8))
art=(R/'src/rooftop_turret_data.h').read_text()
pixels=[int(v,16) for v in re.findall(r'0x[0-9a-f]{4}',art)]
assert len(pixels)==576+8*256 and all(v==0 or v&0x8000 for v in pixels)
# Top-down armor must be green-dominant; metallic gun directions are distinct.
assert sum(bool(v) and ((v>>5)&31)>(v&31) and ((v>>5)&31)>((v>>10)&31) for v in pixels[:576])>160
assert len({tuple(pixels[576+i*256:576+(i+1)*256]) for i in range(8)})==8
s=(R/'src/wingsuit.c').read_text();anchors=[tuple(map(int,a)) for a in re.findall(r'\{(\d+),(\d+),(\d+)\}',s[s.index('const mf_ws_roof_anchor'):s.index('void mf_ws_turret_position')])]
assert anchors==[(308,244,1),(343,392,1)]
# Manually audited machinery BODY masks; flat landing-circle paint is a surface,
# not an obstruction. Existing roof/equipment shadows remain unchanged beneath.
obstacles=Image.new('1',(512,512));d=ImageDraw.Draw(obstacles)
d.rectangle((275,187,297,204),fill=1);d.rectangle((324,187,339,202),fill=1)
d.line([(277,278),(277,208),(309,208)],fill=1,width=3)
d.ellipse((291,374,315,398),fill=1);d.ellipse((323,403,349,429),fill=1)
d.line([(300,405),(300,438),(328,438)],fill=1,width=3)
d.rectangle((292,445,327,455),fill=1);d.rectangle((320,370,333,382),fill=1)
for ax,ay,plane in anchors:
 candidates=[]
 for site in m['aerial_city']['sites']:
  if site['plane']!=plane:continue
  mask=Image.new('1',(512,512));ImageDraw.Draw(mask).polygon([tuple(p) for p in site['footprint']],fill=1)
  opaque=[(ax+x-12,ay+y-12) for y in range(24) for x in range(24) if pixels[y*24+x]]
  if all(mask.getpixel(p) for p in opaque):candidates.append(site['name'])
 assert len(candidates)==1,(ax,ay,candidates)
 for p in opaque:assert roof.getpixel(p) and not obstacles.getpixel(p),('unsupported roof/machinery',p)
print('PASS turret scope: %d frozen approved files; Chrome Eye path/spawn/art, camera, Level1, city/audio/workflow unchanged; two native solid rooftop anchors clear of equipment bodies; green top-down base/eight directions; VDP1 33792/28/81, VDP2 65792/434176, CRAM32, SCSP307260 unchanged'%len(lock['frozen']))
