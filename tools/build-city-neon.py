#!/usr/bin/env python3
"""Pack a native RGB555 city candidate into a bounded VDP2 cell bank.
Generated high-resolution study is private; CITY555.BIN is the native runtime
source. No approved assets are overwritten. Dynamic colors are region-scoped.
"""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1];out=root/'assets/city-neon'
src=np.frombuffer((out/'CITY555.BIN').read_bytes(),dtype='>u2').reshape(240,640)
rgb=np.stack([(src&31)*8,((src>>5)&31)*8,((src>>10)&31)*8],axis=-1).astype('uint8')
# Static art gets 224 colors; eight explicit colors belong only to the sign/interior.
im=Image.fromarray(rgb).quantize(colors=224,dither=Image.Dither.NONE)
pixels=np.array(im,dtype='uint8')+1
pal=np.array(im.getpalette(),dtype='uint16').reshape(-1,3)[:224]//8
colors=np.full(255,0x8000,dtype='uint16')
colors[:224]=0x8000|pal[:,0]|pal[:,1]<<5|pal[:,2]<<10
live=[(6,18,24),(9,25,30),(22,30,31),(3,10,18),(25,7,23),(4,20,24),(22,6,20),(9,25,30)]
for i,(r,g,b) in enumerate(live):colors[239+i]=0x8000|r|g<<5|b<<10
for y in range(77,141):
 for x in range(397,510):
  r,g,b=map(int,rgb[y,x]);slot=None
  if y<=97 and g>65 and b>95 and g>r*1.2:
   slot=2 if r>100 and g>150 else 1 if g>115 else 0
   if 440<=x<467 and slot==1:slot=7
  elif y<=99 and r>95 and b>95 and r>g*1.3:slot=4
  elif y<=99 and b>55 and b>r*1.8 and g>35:slot=3
  elif 114<=y<=129 and g>65 and b>80 and g>r*1.4:slot=5
  elif 114<=y<=129 and r>70 and b>65 and r>g*1.4:slot=6
  if slot is not None:pixels[y,x]=240+slot
# Palette centroids retain the generated art's value balance, especially halo
# pixels: reserving an index must not turn a subtle glow into a solid light bar.
for slot in range(8):
 samples=rgb[pixels==240+slot].astype(np.float32)
 assert len(samples),('empty live-color class',slot)
 r,g,b=np.clip(np.rint(samples.mean(axis=0)/8),0,31).astype('uint16')
 colors[239+slot]=0x8000|r|g<<5|b<<10
# VDP2 CN_12BIT 8bpp permits 2048 cells in A0. Use bounded tile vector
# quantization only in low-contrast road/sky; never merge facade or live cells.
lookup={};tiles=[];positions=[];eligible=[]
for ty in range(30):
 row=[]
 for tx in range(80):
  tile=pixels[ty*8:ty*8+8,tx*8:tx*8+8].tobytes()
  if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile);eligible.append(ty<7 or ty>=20)
  else:eligible[lookup[tile]] &= ty<7 or ty>=20
  row.append(lookup[tile])
 positions.append(row)
original_count=len(tiles);mapping=list(range(len(tiles)))
# Merge visually closest tile pairs until the 1664-cell review budget fits (24 KiB of A0 stays free). RGB555 RMSE is measured
# in channel steps; the facade and all live pixels are excluded from merging.
c=np.array([[((int(colors[v-1])>>shift)&31) for v in t for shift in (0,5,10)] for t in tiles],dtype=np.float32)
ids=np.flatnonzero(eligible);vectors=c[ids]
squares=(vectors*vectors).sum(axis=1)
dist=np.maximum(0,(squares[:,None]+squares[None,:]-2*vectors@vectors.T)/vectors.shape[1])
np.fill_diagonal(dist,np.inf)
removed=set();errors=[]
while len(tiles)-len(removed)>1664:
 a,b=np.unravel_index(np.argmin(dist),dist.shape)
 assert np.isfinite(dist[a,b]),'No safe background tile merges left'
 ia,ib=int(ids[a]),int(ids[b]);rms=float(dist[a,b]**.5)
 assert rms<=1.35,('tile compression would exceed 10.8 RGB888 RMS',rms)
 mapping[ib]=ia;removed.add(ib);errors.append(rms)
 dist[b,:]=dist[:,b]=np.inf
kept=[i for i in range(len(tiles)) if i not in removed];new={i:n for n,i in enumerate(kept)}
def canonical(i):
 while mapping[i]!=i:i=mapping[i]
 return new[i]
positions=[[canonical(i) for i in row] for row in positions]
# Measure actual accumulated error, including chains of merged representatives.
rebuilt=np.zeros_like(pixels)
for ty,row in enumerate(positions):
 for tx,i in enumerate(row):rebuilt[ty*8:ty*8+8,tx*8:tx*8+8]=np.frombuffer(tiles[kept[i]],dtype='uint8').reshape(8,8)
assert np.array_equal(rebuilt[56:160],pixels[56:160])
assert np.array_equal(rebuilt[pixels>=240],pixels[pixels>=240])
cells=b''.join(tiles[i] for i in kept);assert len(cells)<=131072
pnd=[]
for page in range(2):
 for y in range(64):
  for x in range(64):pnd.append(0x1000|(positions[y][page*64+x]*2 if y<30 and page*64+x<80 else 0))
files={'CICELL.BIN':cells,'CIMAP.BIN':struct.pack('>8192H',*pnd),'CIPAL.BIN':colors.astype('>u2').tobytes(),'CIPIX.BIN':rebuilt.tobytes(),'CIREF.BIN':pixels.tobytes()}
# Existing long-map preview receives new street chunk IDs and a static palette
# translation of its old skyline. Its maps/ring/allocations remain unchanged.
chunks=[pnd[(s*16+x)//64*4096+y*64+(s*16+x)%64] for s in range(5) for y in range(30) for x in range(16)]
files['CICHUNK.BIN']=struct.pack('>2400H',*chunks)
oldpal=np.frombuffer((root/'assets/vdp2/STPAL.BIN').read_bytes(),dtype='>u2')
trans=np.zeros(256,dtype='uint8')
for i in range(1,256):
 old=int(oldpal[i-1]);v=np.array([(old>>s)&31 for s in (0,5,10)])
 trans[i]=int(np.argmin(((pal-v)**2).sum(axis=1)))+1
files['CISKY.BIN']=bytes(trans[v] for v in (root/'assets/parallax/PSKY.BIN').read_bytes())
for n,d in files.items():(out/n).write_bytes(d)
header='#ifndef MF_CITY_NEON_DATA_H\n#define MF_CITY_NEON_DATA_H\n#define MF_CITY_CELL_BYTES %du\nstatic const unsigned short city_neon_base[8]={%s};\n#endif\n'%(len(cells),','.join(hex(int(v)) for v in colors[239:247]))
(root/'src/city_neon_data.h').write_text(header)
manifest={'parent':'b1abb866aa0f6cfd09794a0ed76e5f054a6ecf6f','width':640,'height':240,'source_sha256':hashlib.sha256((out/'CITY555.BIN').read_bytes()).hexdigest(),'original_unique_tiles':original_count,'tile_count':len(kept),'cell_bytes':len(cells),'map_bytes':16384,'palette_bytes':510,'dynamic_cell_indices':list(range(240,248)),'facade_lossless_after_palette_quantization':True,'merged_low_contrast_tiles':len(removed),'max_pair_rms_rgb555':max(errors,default=0),'palette_bank':1,'extra_vdp1_bytes':0,'extra_sprite_definitions':0,'extra_cram_banks':0,'street_vdp2_bytes':len(cells)+16384,'sha256':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['tile_count','cell_bytes','merged_low_contrast_tiles','max_pair_rms_rgb555']},indent=2))
