#!/usr/bin/env python3
"""Losslessly compile the five existing indexed street TGAs to VDP2 cells/maps.
No resampling, quantization, artwork generation, or original asset writes.
"""
from pathlib import Path
import hashlib,json,struct

root=Path(__file__).resolve().parents[1]
out=root/'assets/vdp2';out.mkdir(exist_ok=True)
rows=[bytearray() for _ in range(240)];palette=None;sources={}
for i in range(5):
    name=f'ST{i}.TGA';d=(root/'assets/cd'/name).read_bytes()
    assert d[:3]==b'\0\1\1' and d[16:18]==b'\x08\0'
    assert struct.unpack_from('<HH',d,12)==(128,240)
    assert len(d)==786+128*240
    if palette is None:palette=d[18:786]
    assert d[18:786]==palette
    sources[name]=hashlib.sha256(d).hexdigest()
    for y in range(240):
        raw=d[786+(239-y)*128:786+(240-y)*128]
        assert min(raw)>0 and max(raw)<254
        # Same +1 mapping used by Jo's existing indexed TGA sprite loader.
        rows[y].extend(v+1 for v in raw)
lookup={};tiles=[];positions=[]
for ty in range(30):
    row=[]
    for tx in range(80):
        tile=b''.join(bytes(rows[ty*8+y][tx*8:tx*8+8]) for y in range(8))
        if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
        row.append(lookup[tile])
    positions.append(row)
cells=b''.join(tiles);assert len(tiles)==1410 and len(cells)==90240
# 1-word PND, CN_12BIT, 8bpp: character addresses are in 32-byte units.
# Palette bank 1 is retained by allocating the street palette first, as before.
mapping=[]
for page in range(2):
    for y in range(64):
        for x in range(64):
            world_x=page*64+x
            index=positions[y][world_x] if y<30 and world_x<80 else 0
            mapping.append(0x1000|index*2)
map_bytes=struct.pack('>8192H',*mapping)
colors=[]
for i in range(255):
    b,g,r=palette[i*3:i*3+3]
    colors.append(0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10))
pal_bytes=struct.pack('>255H',*colors)
files={'STCELLS.BIN':cells,'STMAP.BIN':map_bytes,'STPAL.BIN':pal_bytes}
for name,data in files.items():(out/name).write_bytes(data)
manifest=dict(source_sha256=sources,width=640,height=240,tile_count=len(tiles),
    cell_bytes=len(cells),map_bytes=len(map_bytes),palette_bytes=len(pal_bytes),
    street_vdp2_bytes=len(cells)+len(map_bytes),sdk_protected_bytes=262144,
    reserved_vdp2_bytes=len(cells)+len(map_bytes)+262144,
    vdp1_recovered_bytes=153600,palette_bank=1,
    sha256={n:hashlib.sha256(d).hexdigest() for n,d in files.items()})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Street: 1410 exact tiles; 90240 cell + 16384 map bytes; 153600 VDP1 bytes recovered.')
