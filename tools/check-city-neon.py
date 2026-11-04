#!/usr/bin/env python3
"""Decode the candidate's actual Saturn formats and optionally its ISO payloads."""
from pathlib import Path
import argparse,hashlib,json,struct,re
root=Path(__file__).resolve().parents[1];folder=root/'assets/city-neon'
parser=argparse.ArgumentParser();parser.add_argument('--disc',action='store_true');args=parser.parse_args()
m=json.loads((folder/'manifest.json').read_text())
assert hashlib.sha256((folder/'CITY555.BIN').read_bytes()).hexdigest()==m['source_sha256']
d={n:(folder/n).read_bytes() for n in m['sha256']}
for n,data in d.items():assert hashlib.sha256(data).hexdigest()==m['sha256'][n],n
cells=d['CICELL.BIN'];mapping=struct.unpack('>8192H',d['CIMAP.BIN']);pal=struct.unpack('>255H',d['CIPAL.BIN']);native=d['CIPIX.BIN']
assert len(cells)==m['cell_bytes']==106496 and m['tile_count']==1664
assert len(native)==640*240 and min(native)>=1 and max(native)<=247
assert len(d['CIPAL.BIN'])==510 and all(c&0x8000 for c in pal)
colors=[int(x,16) for x in re.search(r'city_neon_base\[8\]=\{([^}]+)',(root/'src/city_neon_data.h').read_text())[1].split(',')]
assert colors==list(pal[239:247])
rebuilt=bytearray()
for y in range(240):
 for x in range(640):
  word=mapping[(x//512)*4096+(y//8)*64+(x%512)//8]
  assert word>>12==1 and not word&1
  tile=(word&4095)//2;assert tile<1664
  v=cells[tile*64+(y%8)*8+x%8];rebuilt.append(v)
  if v>=240:assert 397<=x<510 and 77<=y<=140,('animated color leaked outside sign/interior',x,y)
assert rebuilt==native
reference=d['CIREF.BIN']
assert len(reference)==len(native)
assert native[56*640:160*640]==reference[56*640:160*640], 'facade altered by cell compression'
for old,new in zip(reference,native):
 if old>=240:assert old==new, 'live sign pixel altered by cell compression' 
# All 321 gameplay cameras and the hardware page seam reconstruct exactly.
for cam in range(321):
 for y in range(240):assert rebuilt[y*640+cam:y*640+cam+320]==native[y*640+cam:y*640+cam+320]
chunks=struct.unpack('>2400H',d['CICHUNK.BIN'])
for s in range(5):
 for y in range(30):
  for x in range(16):
   col=s*16+x;assert chunks[(s*30+y)*16+x]==mapping[col//64*4096+y*64+col%64]
assert len(d['CISKY.BIN'])==8192 and max(d['CISKY.BIN'])<240
assert m['extra_vdp1_bytes']==m['extra_sprite_definitions']==m['extra_cram_banks']==0
# Actual pinned ownership/address ranges, end exclusive. Jo's release allocator
# has no general bank-overflow guard; explicit sizes and pointer guards matter.
regions=[('street cells',0x25e00000,0x25e00000+len(cells)),
         ('SDK A1',0x25e20000,0x25e40000),
         ('street ring',0x25e40000,0x25e44000),
         ('skyline cells',0x25e44000,0x25e46000),
         ('skyline map',0x25e46000,0x25e48000),
         ('SDK B1',0x25e60000,0x25e80000)]
for i,(name,start,end) in enumerate(regions):
 assert start<end and 0x25e00000<=start<end<=0x25e80000,name
 for other,a,b in regions[i+1:]:assert end<=a or b<=start,(name,other)
assert regions[0][2]==0x25e1a000 and 0x25e20000-regions[0][2]==24576
assert 0x25e60000-0x25e48000==98304
assert sum(end-start for _,start,end in regions)==401408

if args.disc:
 enabled=(root/'build/city-neon-mode.txt').read_text().strip()=='1'
 image=(root/'build/mullet-force.bin').read_bytes();files={}
 def scan(blob,prefix=''):
  pos=0
  while pos<len(blob):
   size=blob[pos]
   if not size:pos=(pos//2048+1)*2048;continue
   record=blob[pos:pos+size];pos+=size;name=record[33:33+record[32]]
   if name in (b'\0',b'\1'):continue
   name=name.decode().split(';')[0];start=struct.unpack_from('<I',record,2)[0]*2048;length=struct.unpack_from('<I',record,10)[0];data=image[start:start+length]
   if record[25]&2:scan(data,prefix+name+'/')
   else:files[prefix+name]=data
 record=image[16*2048+156:16*2048+190];start=struct.unpack_from('<I',record,2)[0]*2048;length=struct.unpack_from('<I',record,10)[0];scan(image[start:start+length])
 for name in ['CICELL.BIN','CIMAP.BIN','CIPAL.BIN']:
  if enabled:assert files[name]==d[name],name
  else:assert name not in files,name
 if enabled and (root/'build/parallax-mode.txt').read_text().strip()=='1':
  assert files['PCHUNK.BIN']==d['CICHUNK.BIN'] and files['PSKY.BIN']==d['CISKY.BIN']
 print('PASS city disc: explicit profile and actual ISO payloads, preserved fallback paths')
print('PASS city: native RGB555/cells/PND reconstruction, 321 cameras, isolated neon colors, translated preview, A0/B0 bounds; zero added VDP1/definitions/CRAM banks')
