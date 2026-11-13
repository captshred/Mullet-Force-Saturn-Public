#!/usr/bin/env python3
"""Pack authored Phase 2 scenery, freezing original pixels and used colors.
No tile vector quantization or global palette reduction. A bounded A0 cache
streams exact indexed tiles from a load-time CPU source; original assets stay.
"""
from pathlib import Path
from PIL import Image
import hashlib,json,struct
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'assets/level1-neon-strip';B=R/'assets/city-cleanup'
old=np.frombuffer((B/'CIPIX.BIN').read_bytes(),dtype=np.uint8).reshape(240,640)
words=np.frombuffer((O/'SOURCE555.BIN').read_bytes(),dtype='>u2').reshape(240,640)
source=np.stack([(words>>s)&31 for s in (0,5,10)],axis=-1).astype(np.int32)
palette=np.array([0,*struct.unpack('>255H',(B/'CIPAL.BIN').read_bytes())],dtype=np.uint16)
used=set(old.ravel())|set((R/'assets/city-gameplay-parallax/LCSKY.BIN').read_bytes())|set((B/'CISKY.BIN').read_bytes())
free=[i for i in range(1,256) if i not in used];assert len(free)==23
inks=[(1,5,2),(2,8,3),(3,12,4),(4,17,5),(5,22,7),(8,27,11),(14,31,17),(20,31,23),
 (9,3,0),(14,5,1),(20,9,1),(26,14,2),(31,19,4),(31,24,8),(31,29,15),(31,31,25),
 (10,1,3),(17,1,4),(24,2,4),(31,4,6),(31,12,11),(7,15,8),(12,22,13)]
assert len(inks)==len(free)
for i,(r,g,b) in zip(free,inks):palette[i]=0x8000|r|(g<<5)|(b<<10)
colors=np.stack([(palette>>s)&31 for s in (0,5,10)],axis=-1).astype(np.int32)
static=[i for i in range(1,256) if i not in range(240,248)]
# Exact RGB555 nearest-color mapping, no dithering. Original world is never quantized.
ext=np.empty((240,640),dtype=np.uint8)
for y in range(240):ext[y]=np.array(static)[((source[y,:,None,:]-colors[None,static,:])**2).sum(axis=-1).argmin(axis=1)]
# Original skyline is rendered independently. Keep native sky/sidewalk source
# tiles for the ring as well; sidewalk/collision horizon is exact at the join.
ext[:56]=old[:56];ext[152:164]=old[152:164]
# Existing pink palette oscillators illuminate only the new liquor marquee/
# OPEN tubing; green/gold use reclaimed previously-unused colors.
for y in range(75,118):
 for x in range(352,624):
  r,g,b=source[y,x]
  if r>=17 and b>=12 and r>g*1.6 and b>g*1.6:ext[y,x]=244 if g>6 else 246
pixels=np.concatenate((old,ext),axis=1);assert np.array_equal(pixels[:,:640],old)
# Original tile IDs/payload stay first, allowing exact initial cache residency.
base=(B/'CICELL.BIN').read_bytes();tiles=[base[i:i+64] for i in range(0,len(base),64)];lookup={t:i for i,t in enumerate(tiles)};positions=[]
for ty in range(30):
 row=[]
 for tx in range(160):
  t=pixels[ty*8:ty*8+8,tx*8:tx*8+8].tobytes()
  if t not in lookup:lookup[t]=len(tiles);tiles.append(t)
  row.append(lookup[t])
 positions.append(row)
assert len(tiles)<4096
chunks=[positions[y][s*16+x] for s in range(10) for y in range(30) for x in range(16)]
files={'NSPIX.BIN':pixels.tobytes(),'NSCELL.BIN':b''.join(tiles),'NSMAP.BIN':struct.pack('>4800H',*chunks),'NSPAL.BIN':palette[1:].astype('>u2').tobytes()}
for name,data in files.items():(O/name).write_bytes(data)
manifest=dict(parent='0de58676e2cb703f6e68552cc46ca0ec03809110',width=1280,height=240,tile_count=len(tiles),original_tiles=1664,new_tiles=len(tiles)-1664,source_cell_bytes=len(tiles)*64,resident_tiles=1664,resident_cell_bytes=106496,map_bytes=16384,chunk_bytes=9600,VDP2_reserved_bytes=434176,VDP2_delta_bytes=0,static_CPU_bytes=4+len(tiles)*64+8+9604+2*len(tiles)+2*1664+len(tiles),new_palette_indices=free,animated_indices=list(range(240,248)),palette_bytes=510,extra_cram_banks=0,extra_VDP1_bytes=0,extra_SCSP_bytes=0,original_pixel_sha256=hashlib.sha256(old.tobytes()).hexdigest(),source_sha256=hashlib.sha256((O/'SOURCE555.BIN').read_bytes()).hexdigest(),sha256={n:hashlib.sha256(d).hexdigest() for n,d in files.items()})
# CPU bytes include NUL/alignment pads for Jo file reads, maps and cache tables.
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(R/'src/neon_strip_data.h').write_text('#ifndef MF_NEON_STRIP_DATA_H\n#define MF_NEON_STRIP_DATA_H\n#define MF_NEON_STRIP_TILES %du\n#define MF_NEON_STRIP_SOURCE_BYTES %du\n#define MF_NEON_STRIP_CACHE_TILES 1664u\n#define MF_NEON_STRIP_MAP_BYTES 9600u\n#endif\n'%(len(tiles),len(tiles)*64))
rgb=((colors.astype(np.uint16)*255)//31).astype(np.uint8);im=Image.fromarray(rgb[pixels]);im.save(O/'panorama.png')
# Preview-only raster error evidence (new authored regions only).
mask=np.ones((240,640),bool);mask[:56]=False;mask[152:164]=False
errors=(colors[ext].astype(float)-source)**2
manifest['new_art_RGB555_RMSE']=float(errors[mask].mean()**.5);(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ('tile_count','new_tiles','source_cell_bytes','resident_cell_bytes','VDP2_delta_bytes','static_CPU_bytes','new_art_RGB555_RMSE')},indent=2))
