"""Independent native/raster/palette/memory checks for the refined enemy bank."""
from pathlib import Path
from PIL import Image,ImageChops
import json,struct,hashlib

def validate_corporate_refined(root,files=None):
 a=root/'assets/corporate-punk-refined';m=json.loads((a/'manifest.json').read_text());pal=(a/'palette.bgr24').read_bytes();master=Image.open(a/'idle-0.png').convert('RGBA')
 def visible(q):
  bg=Image.new('RGBA',q.size,(0,0,0,255));bg.alpha_composite(q);return bg.convert('RGB')
 def same(q,r):assert q.size==r.size and q.getchannel('A').tobytes()==r.getchannel('A').tobytes() and visible(q).tobytes()==visible(r).tobytes()
 assert len(pal)==768 and master.size==(96,96) and master.getbbox()==(16,0,80,92) and m['root']==[48,92]
 legacy=(root/'assets/cd/EN00.TGA').read_bytes();oldused=set()
 for p in (root/'assets/cd').glob('EN*.TGA'):oldused.update(p.read_bytes()[786:])
 for i in oldused:assert pal[3*i:3*i+3]==legacy[18+3*i:21+3*i]
 delta=json.loads((a/'palette-delta.json').read_text());added={e['raw_index'] for e in delta['new_entries']};assert not added&oldused and len(added)==220 and max(added)<=253
 def word(i):
  b,g,r=pal[3*i:3*i+3];return (r>>3)|((g>>3)<<5)|((b>>3)<<10)
 assert len({word(i) for i in added|set(range(1,15))})==len(added|set(range(1,15)))
 for e in delta['new_entries']:assert word(e['raw_index'])==e['rgb555']&32767
 decoded=[];unique=set()
 for r in m['resources']:
  b=(a/r['name']).read_bytes();w,h=struct.unpack_from('<HH',b,12)
  assert b[:3]==b'\0\1\1' and b[7]==24 and b[16:18]==b'\10\0' and b[18:786]==pal
  assert (w,h)==(r['width'],r['height']) and w%8==h%2==0 and len(b)==786+w*h and max(b[786:])<=253
  assert hashlib.sha256(b).hexdigest()==r['sha256'] and r['bytes']==(w*h+31)&~31
  key=(w,h,b[786:]);assert key not in unique;unique.add(key)
  q=Image.new('P',(w,h));q.putpalette([v for i in range(256) for v in pal[3*i:3*i+3][::-1]]);q.putdata([v for y in range(h-1,-1,-1) for v in b[786+y*w:786+(y+1)*w]]);q.info['transparency']=0;decoded.append(q.convert('RGBA'))
  if files is not None:assert files[r['name']]==b
 poses=[]
 for f in m['poses']:
  ref=Image.open(a/(f['name']+'.png')).convert('RGBA');assert ref.getbbox()[1]==0 and ref.getbbox()[3]==92 and set(ref.getchannel('A').getdata())=={0,255};poses.append(ref)
  assert len(f['parts'])==4
  for flip in [False,True]:
   out=Image.new('RGBA',(96,96));occupied=set()
   for p in f['parts']:
    q=decoded[p['resource']];assert q.size==(p['width'],p['height'])
    for y in range(q.height):
     for x in range(q.width):
      if q.getpixel((x,y))[3]:assert (p['x']+x,p['y']+y) not in occupied;occupied.add((p['x']+x,p['y']+y))
    if flip:q=q.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    out.alpha_composite(q,(96-p['x']-q.width if flip else p['x'],p['y']))
   same(out,ref.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else ref)
 same(poses[0],poses[4]);same(poses[0],Image.open(a/'candidate-92.png').convert('RGBA'))
 for f in [1,2]:
  same(poses[f].crop((0,0,96,22)),master.crop((0,0,96,22)));same(poses[f].crop((0,52,96,96)),master.crop((0,52,96,96)));assert poses[f].tobytes()!=master.tobytes()
 for f in [3,5]:same(poses[f].crop((0,0,96,52)),master.crop((0,0,96,52)))
 assert len({q.tobytes() for q in poses[3:]})==3
 for label,group in [('idle',poses[:3]),('walk',poses[3:])]:
  gif=Image.open(a/f'{label}-4x.gif');assert gif.n_frames==3
  for i,q in enumerate(group):gif.seek(i);same(gif.convert('RGBA'),q.resize((384,384),Image.Resampling.NEAREST))
 assert Image.open(a/'candidate-88.png').convert('RGBA').getbbox()[1::2]==(4,92)
 same(Image.open(a/'master-92-8x.png').convert('RGBA'),master.resize((768,768),Image.Resampling.NEAREST))
 lineup=Image.open(a/'lineup-native.png').convert('RGBA')
 for n,x in [('buck',0),('chuck',128)]:
  q=Image.open(root/f'assets/animation-polish/{n}-00.png').convert('RGBA')
  for y in range(96):
   for xx in range(q.width):
    v=q.getpixel((xx,y))
    if v[3]:assert lineup.getpixel((x+xx,y))==v
 for base in ['lineup','contact']:
  q=Image.open(a/f'{base}-native.png').convert('RGBA');same(Image.open(a/f'{base}-4x.png').convert('RGBA'),q.resize((q.width*4,q.height*4),Image.Resampling.NEAREST))
 assert m['texture_bytes']==sum(r['bytes'] for r in m['resources'])==11744 and m['texture_slots']==len(decoded)==10
 assert m['boot_bytes']==362848 and m['boot_free']==95640 and m['full_bytes']==438848 and m['full_free']==19640 and m['boot_slots']==135
 assert m['idle_holds']==[24,12,18] and m['walk_holds']==[7,7,7]
 assert m['palette_opaque_colors']==len({word(v) for v in Image.open(a/'idle-0.png').getdata() if v})==180
 for n,h in m['source_sha256'].items():assert hashlib.sha256((a/'source'/n).read_bytes()).hexdigest()==h
 print('PASS refined Corporate Punk:92px/native88 comparison, fixed head/torso/idle feet, distinct gait, binary alpha, exact TGAs/mirrors/GIFs/lineup, legacy palette preserved,10 deduplicated textures/11744 bytes')
 return m
if __name__=='__main__':validate_corporate_refined(Path(__file__).resolve().parents[1])
