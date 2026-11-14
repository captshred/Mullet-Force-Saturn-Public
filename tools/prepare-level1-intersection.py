#!/usr/bin/env python3
"""Deterministic, lossless 1920px pack; approved 1280px/palette stay exact.
The new native indexed EXTPIX is the runtime art input. High-resolution
image-generation sources are private and are not needed by builds.
"""
from pathlib import Path
import hashlib,json,struct,heapq
from collections import Counter
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'assets/level1-intersection';B=R/'assets/level1-neon-strip'
BASE='43cd82d33dd6195a036f9775f8b0e961fedbe9bb'
def tokenize(b):
 tokens=[];history={};i=0
 while i<len(b):
  best=0;distance=0
  for j in reversed(history.get(b[i:i+3],[])):
   n=3
   while n<66 and i+n<len(b) and b[i+n]==b[j+n]:n+=1
   if n>best:best=n;distance=i-j
   if best==66:break
  n=best if best>=3 else 1
  tokens.append((256+best-3,distance-1) if best>=3 else (b[i],None))
  for k in range(i,i+n):history.setdefault(b[k:k+3],[]).append(k)
  i+=n
 return tokens
old=np.frombuffer((B/'NSPIX.BIN').read_bytes(),np.uint8).reshape(240,1280)
ext=np.frombuffer((O/'EXTPIX.BIN').read_bytes(),np.uint8).reshape(240,640)
pixels=np.concatenate((old,ext),axis=1);assert np.array_equal(pixels[:,:1280],old)
base=(B/'NSCELL.BIN').read_bytes()
render=pixels.copy();render[:56,:1280]=0 # These cells expose the unchanged parallax layer.
needed={render[y:y+8,x:x+8].tobytes() for y in range(0,240,8) for x in range(0,1920,8)}
tiles=[base[i:i+64] for i in range(0,len(base),64) if base[i:i+64] in needed]
lookup={v:i for i,v in enumerate(tiles)};positions=[]
for y in range(30):
 row=[]
 for x in range(240):
  tile=render[y*8:y*8+8,x*8:x*8+8].tobytes()
  if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
  row.append(lookup[tile])
 positions.append(row)
assert len(tiles)<32768 and bytes(64) in lookup
chunks=[positions[y][s*16+x] for s in range(15) for y in range(30) for x in range(16)]
raw=b''.join(tiles);blocks=[tokenize(raw[i:i+512].ljust(512,b'\0')) for i in range(0,len(raw),512)]
frequencies=Counter(symbol for block in blocks for symbol,_ in block)
heap=[(n,symbol,symbol) for symbol,n in sorted(frequencies.items())];heapq.heapify(heap);serial=320
while len(heap)>1:
 a,b=heapq.heappop(heap),heapq.heappop(heap)
 heapq.heappush(heap,(a[0]+b[0],serial,(a[2],b[2])));serial+=1
root=heap[0][2];tree=[];codes={}
def visit(node,code=0,bits=0):
 if isinstance(node,int):codes[node]=(code,bits);return -node-1
 at=len(tree);tree.append(None);left=visit(node[0],code*2,bits+1);right=visit(node[1],code*2+1,bits+1);tree[at]=(left,right);return at
assert visit(root)==0
packed=bytearray();offsets=[]
for block in blocks:
 offsets.append(len(packed));value=0;bits=0
 def emit(v,n):
  global value,bits
  value=(value<<n)|v;bits+=n
  while bits>=8:
   bits-=8;packed.append((value>>bits)&255);value&=(1<<bits)-1
 for symbol,distance in block:
  emit(*codes[symbol])
  if distance is not None:emit(distance,9)
 if bits:packed.append((value<<(8-bits))&255)
offsets.append(len(packed));data_bytes=len(packed)
packed.extend(bytes((-len(packed))%4)) # SGL DMA requires word-sized transfers.
files={'IXPIX.BIN':pixels.tobytes(),'IXPACK.BIN':bytes(packed),'IXOFF.BIN':struct.pack('>'+str(len(offsets))+'I',*offsets),'IXMAP.BIN':struct.pack('>7200H',*chunks)}
for n,b in files.items():(O/n).write_bytes(b)
manifest=dict(parent=BASE,width=1920,height=240,original_width=1280,tile_count=len(tiles),original_tiles=3424,retained_original_visible_tiles=sum(base[i:i+64] in needed for i in range(0,len(base),64)),new_tiles=len(tiles)-sum(base[i:i+64] in needed for i in range(0,len(base),64)),raw_source_bytes=len(raw),packed_source_bytes=len(packed),packed_data_bytes=data_bytes,offset_bytes=len(offsets)*4,codec='block512-LZ512-Huffman',huffman_nodes=len(tree),huffman_max_bits=max(b for _,b in codes.values()),block_bytes=512,block_count=len(offsets)-1,blank_tile=lookup[bytes(64)],chunk_bytes=14400,resident_tiles=1664,resident_cell_bytes=106496,map_bytes=16384,VDP2_reserved_bytes=434176,VDP2_delta_bytes=0,VDP1_delta_bytes=0,SCSP_delta_bytes=0,decode_cache_heap_bytes=65536+len(blocks)*4+(len(blocks)+7)//8,decode_cache_metadata_bytes=128*6+28,palette_sha256=hashlib.sha256((B/'NSPAL.BIN').read_bytes()).hexdigest(),original_pixel_sha256=hashlib.sha256(old.tobytes()).hexdigest(),extension_sha256=hashlib.sha256(ext.tobytes()).hexdigest(),sha256={n:hashlib.sha256(b).hexdigest() for n,b in files.items()})
manifest['static_CPU_bytes']=len(packed)+4+len(offsets)*4+4+14404+2*len(tiles)+2*1664+(len(tiles)+7)//8+512+16+len(tree)*4+128*6+28
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(R/'src/intersection_data.h').write_text('''#ifndef MF_INTERSECTION_DATA_H
#define MF_INTERSECTION_DATA_H
#define MF_INTERSECTION_TILES %du
#define MF_INTERSECTION_PACK_BYTES %du
#define MF_INTERSECTION_PACK_DATA_BYTES %du
#define MF_INTERSECTION_OFFSET_BYTES %du
#define MF_INTERSECTION_BLOCKS %du
#define MF_INTERSECTION_BLANK %du
#define MF_INTERSECTION_MAP_BYTES 14400u
#define MF_INTERSECTION_CACHE_TILES 1664u
#define MF_INTERSECTION_WIDTH 1920
#define MF_INTERSECTION_HUFF_NODES %du
static const short mf_intersection_huffman[MF_INTERSECTION_HUFF_NODES][2]={%s};
#endif
'''%(len(tiles),len(packed),data_bytes,len(offsets)*4,len(offsets)-1,lookup[bytes(64)],len(tree),','.join('{%d,%d}'%v for v in tree)))
pal=np.array([0,*struct.unpack('>255H',(B/'NSPAL.BIN').read_bytes())]);colors=np.stack([((pal>>s)&31)*255//31 for s in (0,5,10)],axis=-1).astype(np.uint8)
D=R/'docs/level1-intersection-phase3a';D.mkdir(parents=True,exist_ok=True)
preview=pixels.copy()
for y in range(56):
 for x in range(1280,1920):
  if preview[y,x]==0:preview[y,x]=old[y,(x-1280)%640]
Image.fromarray(colors[preview]).save(D/'panorama.png');Image.fromarray(colors[preview[:,1280:]]).save(D/'intersection-640.png');Image.fromarray(colors[preview[:,1088:1536]]).save(D/'liquor-transition.png');Image.fromarray(colors[preview[:,1440:1760]]).save(D/'intersection-native.png')
print(json.dumps(manifest,indent=2))
