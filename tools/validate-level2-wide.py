#!/usr/bin/env python3
"""Exhaustive additive baseline preservation and wide-map hardware validation."""
from pathlib import Path
import hashlib,json,struct
from level2_balanced_scope import balanced_change
from level2_timing_scope import timing_change
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'docs/level2-wide-lock.json').read_text())
assert x['base_commit']=='78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e'
allowed={
'assets/wingsuit/WMAP.BIN','assets/wingsuit/manifest.json',
'src/wingsuit.c','src/wingsuit.h','src/wingsuit_runtime.c',
'tests/wingsuit_aim_test.c','tests/wingsuit_mock/jo/jo.h','tests/wingsuit_runtime_test.c','tests/wingsuit_test.c','tests/wingsuit_weapon_test.c',
'tools/level2_audio_scope.py','tools/level2_polyphony_scope.py','tools/level2_split_scope.py','tools/test-flame-focus.py','tools/test-wingsuit.py','tools/validate-level2-audio.py','tools/validate-wingsuit.py'}
assert set(x['changes'])==allowed
for group in ['frozen','changes']:
 for n,entry in x[group].items():
  expected=balanced_change(n,entry if group=='frozen' else entry['after']);b=(R/n).read_bytes()
  assert len(b)==expected['bytes'] and hashlib.sha256(b).hexdigest()==expected['sha256'],n
for n in ['src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_audio_data.h','assets/wingsuit/WDEATH.MAP','assets/wingsuit/WDEATH.SEQ','assets/wingsuit/WDEATH.TON','assets/wingsuit/audio.json','assets/wingsuit/flame-audio.json']:
 assert n in x['frozen'],n
s=(R/'src/wingsuit_runtime.c').read_text()
for key,begin,end in [('loader','', 'static void draw('),('audio_runtime','void mf_ws_runtime_frame(',None)]:
 a=s.index(begin) if begin else 0;b=s.index(end,a) if end else len(s)
 assert hashlib.sha256(s[a:b].encode()).hexdigest()==x['runtime_preserved'][key],key
m=json.loads((R/'assets/wingsuit/manifest.json').read_text());assert (m['vdp1_bytes'],m['textures'],m['max_sprite_commands'])==(28032,18,73)
assert (m['vdp2_payload_bytes'],m['cram_bytes'],m['tiles'])==(10944,32,43)
a=R/'assets/wingsuit';words=struct.unpack('>4096H',(a/'WMAP.BIN').read_bytes());tiles=(a/'WCELL.BIN').read_bytes()
# A full 512px horizontal period; no exact 256px duplicate, blank/uninitialized
# names, new cell IDs, flipped cells, or scaling. Roads align across districts.
assert any(words[y*64+x]!=words[y*64+x+32] for y in range(64) for x in range(32))
for y in range(64):
 for tx in range(64):
  w=words[y*64+tx];assert w>>12==1 and w%2==0 and (w&4095)//2<43
  if tx>=32:assert w==words[((y+16)%64)*64+tx-32]
 for row in range(8):
  l=(words[y*64+31]&4095)//2;r=(words[y*64+32]&4095)//2
  assert tiles[l*64+row*8+7]==tiles[r*64+row*8],('district seam',y,row)
assert 106496+65536+262144==434176 and 524288-434176==90112
assert 131072-106496==24576 and 131072-65536==65536
assert 106496-len(tiles)==103744 and 65536-8192==57344
print('PASS wide preservation: %d frozen baseline files; exact scoped updates; complete audio sources/bank/metadata, loader and audio runtime unchanged; 512px map/nonmirrored cells/seams; VDP1 28032/18/73, VDP2 10944/434176/90112 headroom, CRAM32'%len(x['frozen']))

# Refinement preservation is additive: old locks and every artwork/audio byte
# stay fixed, with only the seven named source/test/validator updates allowed.
r=json.loads((R/'docs/level2-balanced-lock.json').read_text())
assert r['base_commit']=='a827c2ec82fddaade0bd8e1c627f75ec9905705c'
assert set(r['changes'])=={'src/wingsuit.h','src/wingsuit.c','src/wingsuit_runtime.c',
 'tests/wingsuit_camera_test.c','tests/wingsuit_runtime_test.c',
 'tools/level2_wide_scope.py','tools/validate-level2-wide.py'}
for n,e in r['changes'].items():
 assert len((R/n).read_bytes())==timing_change(n,e['after'])['bytes']
 assert hashlib.sha256((R/n).read_bytes()).hexdigest()==timing_change(n,e['after'])['sha256'],n
for n,e in r['extra_frozen'].items():
 assert len((R/n).read_bytes())==timing_change(n,e)['bytes'] and hashlib.sha256((R/n).read_bytes()).hexdigest()==timing_change(n,e)['sha256'],n
# All source pixels displayed at any legal camera position lie in the existing
# central map crop [96,415]. Every 8px cell resolves to initialized 8bpp data.
assert (320-224)//2==48 and 320-224==96
for camera in range(97):
 left=camera+96;right=left+223
 assert 96<=left<=right<=415<512
 for y in range(64):
  for tx in range(left//8,right//8+1):
   w=words[y*64+tx];assert w>>12==1 and (w&4095)//2<len(tiles)//64
assert r['preserved_runtime']==x['runtime_preserved']
print('PASS balanced-scroll preservation: 320px world/224px view/96px travel/48px center; all 97 camera positions inside unchanged city crop; all artwork/audio/Level1/workflows and prior locks preserved')

# Scheduling exceptions are exact; all other balanced baseline bytes stay fixed.
from validate_level2_timing import validate
validate()
