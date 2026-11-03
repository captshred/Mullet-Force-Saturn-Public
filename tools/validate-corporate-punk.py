#!/usr/bin/env python3
"""Independent offline checks: exported pixels, legacy palette and assembly."""
from pathlib import Path
from PIL import Image, ImageChops
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];A=R/'assets/corporate-punk';m=json.loads((A/'manifest.json').read_text())
def same(a,b):assert a.size==b.size and a.tobytes()==b.tobytes()
def visible(q):
 b=Image.new('RGBA',q.size,(0,0,0,255));b.alpha_composite(q);return b.convert('RGB')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=Image.open(A/'corporate-punk-84.png');im=p.convert('RGBA');assert p.mode=='P' and p.size==(96,96)
assert im.getbbox()==(25,8,72,92) and set(im.getchannel('A').getdata())=={0,255}
used=set(p.getdata())-{0};assert len(used)==42 and max(used)<=253
pal=(A/'palette.bgr24').read_bytes();assert len(pal)==768
old=(R/'assets/cd/EN00.TGA').read_bytes();oldused=set()
for f in (R/'assets/cd').glob('EN*.TGA'):oldused.update(f.read_bytes()[786:])
for i in oldused:assert pal[3*i:3*i+3]==old[18+3*i:21+3*i]
def hw(i):
 b,g,r=pal[3*i:3*i+3];return (r>>3)|((g>>3)<<5)|((b>>3)<<10)
assert len({hw(i) for i in used})==42
for e in m['added_palette_entries']:assert e['raw_index'] not in oldused and hw(e['raw_index'])==e['rgb555']&32767

def decode(d):
 f=A/d['name'];b=f.read_bytes();assert digest(f)==d['sha256']
 assert b[:3]==bytes([0,1,1]) and struct.unpack_from('<H',b,5)[0]==256 and b[7]==24 and b[16:18]==bytes([8,0])
 w,h=struct.unpack_from('<HH',b,12);assert (w,h)==(d['width'],d['height']) and w%8==h%2==0
 assert b[18:786]==pal and len(b)==786+w*h
 q=Image.new('P',(w,h));q.putpalette([v for i in range(256) for v in pal[3*i:3*i+3][::-1]]);q.putdata([v for y in range(h-1,-1,-1) for v in b[786+y*w:786+(y+1)*w]]);q.info['transparency']=0
 assert d['anchor']==[48-d['x'],92-d['y']]
 return q.convert('RGBA')
for group in [[m['whole_texture']],m['parts']]:
 assembled=Image.new('RGBA',(96,96));mirrored=Image.new('RGBA',(96,96))
 for d in group:
  q=decode(d);assembled.alpha_composite(q,(d['x'],d['y']));mirrored.alpha_composite(q.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(96-d['x']-d['width'],d['y']))
 # Transparent RGB is irrelevant to hardware rendering.
 assert ImageChops.difference(assembled.getchannel('A'),im.getchannel('A')).getbbox() is None
 assert ImageChops.difference(visible(assembled),visible(im)).getbbox() is None
 assert ImageChops.difference(visible(mirrored),visible(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT))).getbbox() is None
 assert mirrored.getchannel('A').tobytes()==im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).getchannel('A').tobytes()
assert sum(d['aligned_bytes'] for d in m['parts'])==m['texture_bytes']==3200
assert [(v['pieces'],v['texture_bytes']) for v in m['layout_candidates']]==[(1,4032),(2,3488),(3,3200),(4,3104)]
for v in m['instance_costs'].values():assert v['shared_texture_bytes']==3200 and v['additional_texture_bytes_per_instance']==0
same(Image.open(A/'corporate-punk-84-rgba.png'),im)
same(Image.open(A/'corporate-punk-84-8x.png'),im.resize((768,768),Image.Resampling.NEAREST))
line=Image.open(A/'lineup-native.png').convert('RGBA')
for n,x in [('buck',0),('chuck',128)]:
 f=R/f'assets/animation-polish/{n}-00.png';assert digest(f)==m['player_sha256'][n]
 q=Image.open(f).convert('RGBA');assert q.getbbox()[3]-q.getbbox()[1]==88
 for y in range(96):
  for xx in range(128):
   v=q.getpixel((xx,y))
   if v[3]==255:assert line.getpixel((xx+x,y))==v
for base,scale in [('lineup',6),('legacy-compare',6)]:
 q=Image.open(A/f'{base}-native.png');same(Image.open(A/f'{base}-{scale}x.png'),q.resize((q.width*scale,q.height*scale),Image.Resampling.NEAREST))
assert Image.open(A/'legacy-en00.png').getbbox()==(0,0,49,90)
for name,h in m['source_sha256'].items():assert digest(A/'source'/name)==h
assert m['active_vdp1_change']==m['active_game_palette_changes']==0 and m['current_playable_allocated']+m['current_playable_free']==458488
print('PASS: native bounds, binary alpha, RGB555 palette preservation, TGA decoding, seam-free assembly/mirroring, shared memory, exact hero lineup, source hashes and NN previews')
