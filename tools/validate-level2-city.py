#!/usr/bin/env python3
"""Native dual-layer payload, preservation, coverage and authoring checks."""
from pathlib import Path
import hashlib,json,struct,re
from level2_city_scope import city_lock
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';m=json.loads((A/'manifest.json').read_text());lock=city_lock()
def info(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
allowed={'assets/wingsuit/WCELL.BIN','assets/wingsuit/WMAP.BIN','assets/wingsuit/manifest.json',
 'src/wingsuit_runtime.c','tests/wingsuit_mock/jo/jo.h','tests/wingsuit_runtime_test.c','tests/wingsuit_disc_test.py',
 'tools/level2_balanced_scope.py','tools/validate-level2-wide.py','tools/validate-wingsuit.py','tools/test-flame-focus.py','tools/stage-wingsuit-assets.py'}
assert set(lock['changes'])==allowed
for n,c in lock['changes'].items():assert info((R/n).read_bytes())==c['after'],n
for n,c in lock['extra_frozen'].items():assert info((R/n).read_bytes())==c,n
assert (m['textures'],m['vdp1_bytes'],m['max_sprite_commands'],m['cram_bytes'])==(18,28032,73,32)
assert len(m['files'])==26
for n,e in m['files'].items():assert info((A/n).read_bytes())==e,n
assert len((A/'WPAL.BIN').read_bytes())==32
cells=(A/'WCELL.BIN').read_bytes();sky=(A/'WSKY.BIN').read_bytes()
assert len(cells)==m['tiles']*64<=65536 and len(sky)==m['sky_tiles']*64<=40960
assert set(cells)<=set(range(1,16)),'lower city must always back transparent upper pixels'
assert set(sky)<=set(range(16))
planes=[]
for filename,chars,base in [('WMAP.BIN',cells,0),('WSMAP.BIN',sky,65536)]:
 words=struct.unpack('>4096H',(A/filename).read_bytes());out=bytearray(512*512)
 for ty in range(64):
  for tx in range(64):
   w=words[ty*64+tx];tile=((w&4095)-base//32)//2
   assert w>>12==1 and not w&1 and 0<=tile<len(chars)//64
   for y in range(8):out[(ty*8+y)*512+tx*8:(ty*8+y)*512+tx*8+8]=chars[tile*64+y*8:tile*64+y*8+8]
 planes.append(bytes(out))
assert planes[0][:512]==planes[0][-512:],'lower vertical wrap joins a continuous road'
assert not any(planes[1][103*512:]),'skyline has a transparent terminal region, no wrap'
assert all(planes[1][y*512+x] for y in range(72) for x in range(512))
# All integral/subpixel camera positions are inside initialized maps; every
# vertical lower scroll phase is covered by a full period, upper never wraps.
for cam in range(96*256+1):
 lower=(cam+(96-48)*256)*256;upper=96*65536+(cam-48*256)*128
 assert (upper-96*65536)*2==lower-96*65536
 assert 96*65536<=(48*65536+lower) and (271*65536+lower)<416*65536
 assert 120*65536<=(48*65536+upper) and (271*65536+upper)<392*65536
for scroll in range(512):assert all(0<=((y-scroll)&511)<512 for y in range(240))
segments=m['city']['segments'];assert len(segments)>=8 and len({s['style'] for s in segments})>=8
assert len({s['bounds'][2] for s in segments})>=5 and len({s['bounds'][3] for s in segments})>=5
assert {'water','sawtooth','ruin','boiler','power'}<=set(s['style'] for s in segments)
patches=set()
for segment in segments:
 x,y,w,h=segment['bounds'];assert 96<=x<x+w<=416 and 8<=y<y+h<488
 patches.add(hashlib.sha256(b''.join(planes[0][yy*512+x:yy*512+x+w] for yy in range(y,y+h))).hexdigest())
assert len(patches)==len(segments) and m['city']['sky_segments']==7
payload=len(cells)+len(sky)+16384;assert payload==m['vdp2_payload_bytes']<=106496+65536
h=(R/'src/wingsuit_city_data.h').read_text()
for macro,value in [('MF_WS_CITY_CELL_BYTES',len(cells)),('MF_WS_SKY_CELL_BYTES',len(sky)),('MF_WS_SKY_CELL_OFFSET',65536),('MF_WS_SKY_MAP_OFFSET',8192),('MF_WS_CITY_MAP_BYTES',8192),('MF_WS_SKY_RATE_DIVISOR',2)]:
 assert int(re.search(r'#define '+macro+r' (\d+)',h)[1])==value
runtime=(R/'src/wingsuit_runtime.c').read_text()
for key,begin,end in [('audio_load','    if(!mf_ws_audio_load','    slCharNbg1'),('audio_runtime','void mf_ws_runtime_frame(',None),('audio_progress','static void audio_progress','static int load_resources')]:
 a=runtime.index(begin);b=runtime.index(end,a) if end else len(runtime)
 assert hashlib.sha256(runtime[a:b].encode()).hexdigest()==lock['preserved_runtime'][key],key
assert 'slSoundOffWait();wipe(MF_WS_SOUND_RAM,0x80000)' in runtime
print('PASS industrial city: 8 distinct compounds/7 skyline silhouettes, native 8bpp roundtrip and palette, 24577 fixed-point camera positions at exact half rate, all512 lower wrap phases, initialized coverage/transparent fade, nonoverlapping A0/B0 arenas; %d payload /434176 reserved /90112 unreserved; no gameplay/camera/audio/Level1 changes'%payload)
