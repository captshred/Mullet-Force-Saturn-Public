#!/usr/bin/env python3
"""Pack scoped native cleanup art; retain approved palette and original assets."""
from pathlib import Path
import hashlib,json,struct
r=Path(__file__).resolve().parents[1];out=r/'assets/city-cleanup';base=r/'assets/city-neon'
pixels=(out/'CIPIX.BIN').read_bytes();mask=(out/'PATCHMASK.BIN').read_bytes();old=(base/'CIPIX.BIN').read_bytes()
assert len(pixels)==len(mask)==len(old)==640*240
assert all(a==b for a,b,m in zip(pixels,old,mask) if not m)
assert all(a==b for a,b in zip(pixels,old) if b>=240),'neon pixels must be unchanged'
lookup={};tiles=[];positions=[]
for ty in range(30):
 row=[]
 for tx in range(80):
  tile=b''.join(pixels[(ty*8+y)*640+tx*8:(ty*8+y)*640+tx*8+8] for y in range(8))
  if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
  row.append(lookup[tile])
 positions.append(row)
cells=b''.join(tiles);assert len(tiles)==1664 and len(cells)==106496,'touchups must retain exact cell allocation'
words=[0x1000|(positions[y][page*64+x]*2 if y<30 and page*64+x<80 else 0) for page in range(2) for y in range(64) for x in range(64)]
chunks=[words[(s*16+x)//64*4096+y*64+(s*16+x)%64] for s in range(5) for y in range(30) for x in range(16)]
files={'CICELL.BIN':cells,'CIMAP.BIN':struct.pack('>8192H',*words),'CICHUNK.BIN':struct.pack('>2400H',*chunks),'CIPAL.BIN':(base/'CIPAL.BIN').read_bytes(),'CISKY.BIN':(base/'CISKY.BIN').read_bytes()}
for n,d in files.items():(out/n).write_bytes(d)
(r/'src/city_cleanup_data.h').write_text('#ifndef MF_CITY_CLEANUP_DATA_H\n#define MF_CITY_CLEANUP_DATA_H\n#define MF_CLEANUP_CELL_BYTES %du\n#endif\n'%len(cells))
# Three native RGB555/transparent frames are the prop source of truth.
source=(out/'CANS555.BIN').read_bytes();assert len(source)==3*32*48*2
for i in range(3):
 words=struct.unpack('>1536H',source[i*3072:(i+1)*3072]);rgb=bytearray()
 for v in words:
  rgb.extend(((v>>10&31)*8,(v>>5&31)*8,(v&31)*8) if v else (255,0,255))
 header=bytearray(18);header[2]=2;struct.pack_into('<HH',header,12,32,48);header[16:18]=bytes([24,32])
 (out/f'DR{i}.TGA').write_bytes(bytes(header)+rgb)
names=[*files,'TOUCHUPMASK.BIN','CANS555.BIN','CIPIX.BIN','PATCHMASK.BIN','DR0.TGA','DR1.TGA','DR2.TGA']
m={'parent':'d664f26108f9a958ad1d2ecea3fc2e59a2bba3b9','touchup_parent':'fa4a56b6df13df6eaeaf0f38676e2de448321217','touchup_mask_pixels':sum((out/'TOUCHUPMASK.BIN').read_bytes()),'tile_count':len(tiles),'cell_bytes':len(cells),'vdp2_delta_bytes':len(cells)-106496,'extra_vdp1_bytes':0,'extra_definitions':0,'prop_dimensions':[32,48],'prop_draw_offset':[-16,-46],'mask_pixels':sum(mask),'sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:m[k] for k in ['tile_count','cell_bytes','vdp2_delta_bytes','mask_pixels']}))
