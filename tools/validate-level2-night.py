#!/usr/bin/env python3
"""Actual indexed CRAM lookup, material separation and exact geometry lock."""
from pathlib import Path
import json,hashlib,struct
from level2_night_scope import night_lock
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';m=json.loads((A/'manifest.json').read_text());lock=night_lock()
def info(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
allowed={'assets/wingsuit/WCELL.BIN','assets/wingsuit/WMAP.BIN','assets/wingsuit/WPAL.BIN','assets/wingsuit/WROOF.BIN','assets/wingsuit/manifest.json',
 'src/wingsuit_aerial_data.h','src/wingsuit_runtime.c','tests/wingsuit_mock/jo/jo.h','tests/wingsuit_runtime_test.c',
 'tools/build-topdown-city-v2.py','tools/level2_aerial_scope.py','tools/validate-topdown-city-v2.py','tools/validate-level2-wide.py'}
assert set(lock['changes'])==allowed
for n,e in lock['changes'].items():assert info((R/n).read_bytes())==e['after'],n
for n,e in lock['extra_frozen'].items():assert info((R/n).read_bytes())==e,n
assert m['aerial_city']==lock['aerial_city']
# Exact native pixel positions and silhouettes, with only the three newly
# separated material classes mapped back to their parent index assignments.
planes=[]
for cn,mn,offset,key in [('WCELL.BIN','WMAP.BIN',0,'ground'),('WROOF.BIN','WRMAP.BIN',65536,'raised')]:
 c=(A/cn).read_bytes();w=struct.unpack('>4096H',(A/mn).read_bytes());out=bytearray(512*512)
 for ty in range(64):
  for tx in range(64):
   tile=((w[ty*64+tx]&4095)-offset//32)//2
   for y in range(8):out[(ty*8+y)*512+tx*8:(ty*8+y)*512+tx*8+8]=c[tile*64+y*8:tile*64+y*8+8]
 assert info(bytes({10:12,11:12,14:13}.get(v,v) for v in out))==lock['geometry'][key],key+' geometry/material positions changed'
 planes.append(out)
palette=struct.unpack('>16H',(A/'WPAL.BIN').read_bytes())
def channels(v):return v&31,(v>>5)&31,(v>>10)&31
def pink(v):
 r,g,b=channels(v);return r>10 and b>8 and r*4>g*5 and b*4>g*5
assert not any(map(pink,palette)), 'bright-pink environment palette'
def luma(i):
 r,g,b=channels(palette[i]);return 2126*r+7152*g+722*b
assert luma(10)<luma(1)<luma(12)<luma(14)<luma(3)<luma(4)<luma(5)<luma(6)
assert len(set(palette))==16
old=struct.unpack('>16H',bytes.fromhex(lock['old_palette_hex']))
assert pink(old[11]),'documented parent pink road/shadow reproduction'
# The old upload at SDK data=257 makes native index12 read asset index11.
old_cram=[0]*2048;old_cram[257:257+16]=old
assert old_cram[256+12]==old[11] and pink(old_cram[256+12])
new_cram=[0x5555]*2050
for i in range(256,2048):new_cram[i]=0
new_cram[256:272]=palette
assert new_cram[:256]==[0x5555]*256 and new_cram[2048:]==[0x5555]*2
for data in planes:
 for index in set(data):assert new_cram[256+index]==palette[index] and not pink(new_cram[256+index])
source=(R/'src/wingsuit_runtime.c').read_text()
assert '#define WS_CRAM_BASE ((jo_color *)JO_VDP2_CRAM+256)' in source
assert 'background_palette->data!=WS_CRAM_BASE+1' in source
assert 'wipe(WS_CRAM_BASE,7*512)' in source and 'copy_file("WPAL.BIN",WS_CRAM_BASE,32)' in source
for key,begin,end in [('render','static void render(', 'void mf_ws_runtime_frame('),('frame','void mf_ws_runtime_frame(',None),('sprite_state','static int restore_sprite_state','static int copy_file'),('audio_load','    if(!mf_ws_audio_load','    slCharNbg1')]:
 a=source.index(begin);b=source.index(end,a) if end else len(source)
 assert hashlib.sha256(source[a:b].encode()).hexdigest()==lock['runtime_preserved'][key],key
sdk=R/'.deps/joengine/jo_engine/vdp2_malloc.c'
if sdk.exists():
 text=sdk.read_text();assert 'CRAM_PALETTE_SIZE      (256)' in text and '+ CRAM_PALETTE_SIZE + 1;' in text
assert (m['textures'],m['vdp1_bytes'],m['cram_bytes'],m['max_sprite_commands'])==(18,28032,32,73)
print('PASS night palette: real257 SDK/256 native bank mismatch reproduces parent pink index12; aligned colors/shadows10 < alleys1 < asphalt12 < paving14 < steel/concrete; zero pink RGB entries, exact native geometry after material-only reindex, full render/parallax/frame/audio preserved; font and CRAM guards safe')
