#!/usr/bin/env python3
"""Scoped art preservation, actual native formats, and packaged prop/scene checks."""
from pathlib import Path
import argparse,hashlib,json,struct
from stage_preservation import stage_digest
r=Path(__file__).resolve().parents[1];out=r/'assets/city-cleanup';base=r/'assets/city-neon'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');a=p.parse_args()
m=json.loads((out/'manifest.json').read_text());d={n:(out/n).read_bytes() for n in m['sha256']}
for n,v in d.items():assert hashlib.sha256(v).hexdigest()==m['sha256'][n],n
for n,h in json.loads((out/'source-lock.json').read_text()).items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==stage_digest(n,h,'sha256'),n
old=(base/'CIPIX.BIN').read_bytes();pixels=d['CIPIX.BIN'];mask=d['PATCHMASK.BIN'];assert len(old)==len(pixels)==len(mask)==153600
assert sum(mask)==5521 and all(v in (0,1) for v in mask)
for i,(x,y,k) in enumerate(zip(old,pixels,mask)):
 if not k:assert x==y,('outside approved lamp mask',i)
 if x>=240:assert x==y,('neon index changed',i)
assert d['CIPAL.BIN']==(base/'CIPAL.BIN').read_bytes() and d['CISKY.BIN']==(base/'CISKY.BIN').read_bytes()
words=struct.unpack('>8192H',d['CIMAP.BIN']);cells=d['CICELL.BIN'];assert len(cells)==m['cell_bytes']==106496 and m['tile_count']==1664
for y in range(240):
 for x in range(640):
  word=words[x//512*4096+y//8*64+(x%512)//8];assert word>>12==1 and not word&1
  tile=(word&4095)//2;assert tile<1664
  assert cells[tile*64+y%8*8+x%8]==pixels[y*640+x]
chunks=struct.unpack('>2400H',d['CICHUNK.BIN'])
for s in range(5):
 for y in range(30):
  for x in range(16):
   col=s*16+x;assert chunks[(s*30+y)*16+x]==words[col//64*4096+y*64+col%64]
for i in range(3):
 v=d[f'DR{i}.TGA'];assert v[:3]==b'\0\0\2' and struct.unpack_from('<HH',v,12)==(32,48) and v[16:18]==bytes([24,32])
 assert len(v)==18+32*48*3
 rgb=[v[j:j+3] for j in range(18,len(v),3)]
 # Same magenta-key RGB555 path as original props; unchanged canvas/anchor.
 key=bytes([255,0,255]);opaque=[j for j,c in enumerate(rgb) if c!=key]
 assert opaque and all(2<=j%32<30 and 2<=j//32<46 for j in opaque)
 assert len(set(rgb))>20
assert m['extra_vdp1_bytes']==m['extra_definitions']==m['vdp2_delta_bytes']==0
if a.disc:
 image=(r/'build/mullet-force.bin').read_bytes();files={}
 def scan(blob):
  pos=0
  while pos<len(blob):
   n=blob[pos]
   if not n:pos=(pos//2048+1)*2048;continue
   rec=blob[pos:pos+n];pos+=n;name=rec[33:33+rec[32]]
   if name in (b'\0',b'\1'):continue
   start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];data=image[start:start+size]
   if not rec[25]&2:files[name.decode().split(';')[0]]=data
 rec=image[16*2048+156:16*2048+190];start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0];scan(image[start:start+size])
 enabled=(r/'build/city-cleanup-mode.txt').read_text().strip()=='1'
 for n in ['CICELL.BIN','CIMAP.BIN','CIPAL.BIN','DR0.TGA','DR1.TGA','DR2.TGA']:
  expected=d[n] if enabled else (base/n).read_bytes() if n.startswith('CI') and (r/'build/city-neon-mode.txt').read_text().strip()=='1' else (r/'assets/cd'/n).read_bytes() if n.startswith('DR') else None
  if expected is not None:assert files[n]==expected,n
print('PASS cleanup: scoped lamp masks, exact surrounding pixels/neon palette, native cell map, 3 same-size/anchor damage frames, immutable behavior/audio/player sources; zero memory delta')
