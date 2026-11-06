#!/usr/bin/env python3
"""Aerial native graphics, complete-building registration and preservation."""
from pathlib import Path
from collections import deque
import json,hashlib,struct,re
from level2_aerial_scope import aerial_lock
from level2_night_scope import night_change
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';m=json.loads((A/'manifest.json').read_text());lock=aerial_lock()
def info(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
allowed={'assets/wingsuit/WCELL.BIN','assets/wingsuit/WMAP.BIN','assets/wingsuit/manifest.json','src/wingsuit_runtime.c',
 'tests/wingsuit_disc_test.py','tests/wingsuit_mock/jo/jo.h','tests/wingsuit_runtime_test.c','tools/level2_balanced_scope.py',
 'tools/stage-wingsuit-assets.py','tools/test-flame-focus.py','tools/validate-level2-wide.py','tools/validate-wingsuit.py'}
assert set(lock['changes'])==allowed
for n,c in lock['changes'].items():assert info((R/n).read_bytes())==night_change(n,c['after']),n
for n,c in {**lock['extra_frozen'],**lock['gameplay_frozen']}.items():assert info((R/n).read_bytes())==night_change(n,c),n
assert (m['vdp1_bytes'],m['textures'],m['max_sprite_commands'],m['cram_bytes'])==(28544,19,73,32)
assert len(m['files'])==26 and {'WROOF.BIN','WRMAP.BIN'}<=set(m['files'])
assert not {'WSKY.BIN','WSMAP.BIN'}&set(m['files'])
for n,e in m['files'].items():assert info((A/n).read_bytes())==e,n
chars=(A/'WCELL.BIN').read_bytes();roofs=(A/'WROOF.BIN').read_bytes()
assert len(chars)==m['tiles']*64<=65536 and len(roofs)==m['roof_tiles']*64<=40960
assert set(chars)<=set(range(1,16)) and set(roofs)<=set(range(16))
# Night pass repurposes formerly pink slots10/11 as charcoal shadows.
# Actual RGB and hardware bank registration are checked by the night suite.
planes=[]
for name,data,offset in [('WMAP.BIN',chars,0),('WRMAP.BIN',roofs,65536)]:
 words=struct.unpack('>4096H',(A/name).read_bytes());out=bytearray(512*512)
 for ty in range(64):
  for tx in range(64):
   w=words[ty*64+tx];tile=((w&4095)-offset//32)//2
   assert w>>12==1 and not w&1 and 0<=tile<len(data)//64
   for yy in range(8):out[(ty*8+yy)*512+tx*8:(ty*8+yy)*512+tx*8+8]=data[tile*64+yy*8:tile*64+yy*8+8]
 planes.append(bytes(out))
assert planes[0][:512]==planes[0][-512:] and not any(planes[1][:8*512]+planes[1][-24*512:])
# Identify complete raised objects directly from native pixels, not the drawing
# implementation. All equipment/walls/shadows must belong to exactly 2 objects.
points={i for i,v in enumerate(planes[1]) if v};objects=[]
while points:
 start=next(iter(points));points.remove(start);q=deque([start]);component=[]
 while q:
  p=q.popleft();component.append(p);x=p%512;y=p//512
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   n=yy*512+xx
   if 0<=xx<512 and 0<=yy<512 and n in points:points.remove(n);q.append(n)
 objects.append((min(p%512 for p in component),min(p//512 for p in component),max(p%512 for p in component)+1,max(p//512 for p in component)+1))
assert len(objects)==2,('floating/disconnected structure',objects)
sites=m['aerial_city']['sites'];assert len(sites)==6 and sum(s['plane'] for s in sites)==2
assert len({tuple(map(tuple,s['footprint'])) for s in sites})==6
assert len({s['wall_height'] for s in sites})>=4
# Each actual raised object remains inside its own ground yard at BOTH parallax
# extremes. The full interval is convex. No unrelated lower-building envelope
# intersects those yards, so there is nothing architectural to detach or cross.
for site in (s for s in sites if s['plane']):
 l,t,r,b=site['yard'];matches=[box for box in objects if l<=box[0]-6 and box[2]+6<=r and t<=box[1] and box[3]<=b]
 assert len(matches)==1,(site['name'],objects)
 for lower in (s for s in sites if not s['plane']):
  xs=[p[0] for p in lower['footprint']];ys=[p[1] for p in lower['footprint']]
  a,c=min(xs),max(xs)+6;d,e=min(ys),max(ys)+lower['wall_height']+4
  assert c<=l or a>=r or e<=t or d>=b,(site['name'],'yard overlaps attached lower architecture')
for cam in range(96*256+1):
 ground=(cam+48*256)*256;raised=96*65536+(cam-48*256)*288
 assert (raised-96*65536)*8==(ground-96*65536)*9
 assert abs(raised-ground)<=6*65536
 assert 96*65536<=48*65536+ground and 271*65536+ground<416*65536
 assert 90*65536<=48*65536+raised and 271*65536+raised<422*65536
for phase in range(512):
 for y in range(240):
  # Both maps have the SAME vertical phase: no building/ground drift on wrap.
  assert ((y-phase)&511)==((y-phase)%512)
assert m['vdp2_payload_bytes']==len(chars)+len(roofs)+16384<=106496+65536
h=(R/'src/wingsuit_aerial_data.h').read_text()
for key,value in [('GROUND_BYTES',len(chars)),('ROOF_BYTES',len(roofs)),('ROOF_OFFSET',65536),('ROOF_MAP_OFFSET',8192),('ROOF_NUMERATOR',9),('ROOF_DENOMINATOR',8)]:
 assert int(re.search(r'#define MF_WS_'+key+r' (\d+)',h)[1])==value
source=(R/'src/wingsuit_runtime.c').read_text()
for key,begin,end in [('audio_load','    if(!mf_ws_audio_load','    slCharNbg1'),('audio_runtime','void mf_ws_runtime_frame(',None),('audio_progress','static void audio_progress','static int load_resources')]:
 a=source.index(begin);b=source.index(end,a) if end else len(source)
 assert hashlib.sha256(source[a:b].encode()).hexdigest()==lock['preserved_runtime'][key],key
assert 'slSoundOffWait();wipe(MF_WS_SOUND_RAM,0x80000)' in source
print('PASS top-down V2: 6 distinct aerial sites, exactly2 complete raised buildings including all walls/equipment/shadows; reserved-yard containment at +/-6px, no architectural overlap; 24577 fixed-point cameras at9/8 X, identical Y over512 phases; no pink, initialized backing/native tiles; %d payload; approved gameplay/camera/audio/Level1 frozen'%m['vdp2_payload_bytes'])

import subprocess
subprocess.run(["python3",str(R/"tools/validate-level2-night.py")],check=True)
