#!/usr/bin/env python3
"""Temporary deterministic skyline and a five-chunk library; never edits source art."""
from pathlib import Path
import hashlib,json,struct
r=Path(__file__).resolve().parents[1];out=r/'assets/parallax';out.mkdir(exist_ok=True)
source=struct.unpack('>8192H',(r/'assets/vdp2/STMAP.BIN').read_bytes())
chunks=[source[((s*16+x)//64)*4096+y*64+(s*16+x)%64] for s in range(5) for y in range(30) for x in range(16)]
pal=(r/'assets/cd/ST0.TGA').read_bytes()[18:786]
def color(rgb):
 return min(range(1,253),key=lambda i:sum((pal[i*3+2-j]-rgb[j])**2 for j in range(3)))+1
sky,wall,edge,lit=map(color,[(8,8,24),(20,20,42),(36,28,58),(70,70,100)])
rows=[bytearray([sky])*512 for _ in range(64)]
for block in range(16):
 x0=block*32+2;roof=12+(block*19+7)%30
 for y in range(roof,64):
  for x in range(x0,x0+27):
   rows[y][x]=edge if x==x0 else (lit if y>roof+3 and y%8 in (1,2) and x%7 in (1,2) else wall)
for x in range(11,512,53):rows[3+x%7][x]=lit
lookup={};tiles=[];ids=[]
for y in range(8):
 for x in range(64):
  tile=b''.join(bytes(rows[y*8+v][x*8:x*8+8]) for v in range(8))
  if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
  ids.append(lookup[tile])
assert len(tiles)<=128
# NBG2 cells in B0+0x4000: low character offset 0x200 (32-byte units).
mapdata=[0x1000|0x200|(ids[y*64+x]*2) if y<8 else 0x1200 for y in range(64) for x in range(64)]
files={'PCHUNK.BIN':struct.pack('>2400H',*chunks),'PSKY.BIN':b''.join(tiles).ljust(8192,b'\0'),'PSMAP.BIN':struct.pack('>4096H',*mapdata)}
for n,d in files.items():(out/n).write_bytes(d)
manifest=dict(world_pixels=8192,chunk_pixels=128,world_chunks=64,source_chunks=5,ring_chunks=8,ring_map_bytes=16384,
 skyline_tiles=len(tiles),skyline_cell_reservation=8192,skyline_map_bytes=8192,extra_vdp2_bytes=16384,
 total_vdp2_reservation=385152,extra_palette_bytes=0,extra_vdp1_bytes=0,skyline_speed_denominator=4,
 indices=[sky,wall,edge,lit],sha256={n:hashlib.sha256(d).hexdigest() for n,d in files.items()})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Parallax: {len(tiles)} skyline tiles in 8192 bytes; 8192 map; 4800 CPU chunk library; no new palette.')
