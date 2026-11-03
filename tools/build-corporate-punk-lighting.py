#!/usr/bin/env python3
"""Exact indexed-color refinement; never generates or resamples a pose."""
from pathlib import Path
from PIL import Image,ImageDraw
from collections import defaultdict
import json,hashlib,copy,struct
R=Path(__file__).resolve().parents[1];B=R/'assets/corporate-punk-refined';A=R/'assets/corporate-punk-lighting';A.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((B/'manifest.json').read_text());pal=bytearray((B/'palette.bgr24').read_bytes());original=bytes(pal);names=[p['name'] for p in base['poses']];frames=[Image.open(B/(n+'.png')).copy() for n in names]
# Explicit audited environmental suit-rim shades. Semantic guards preserve the
# full head and a conservative shirt/tie rectangle even when indices are shared.
rims=[74,100,120,121,146,162,163,175,176,186,187,192]
def protected(x,y):return y<22 or (49<=x<61 and 22<=y<52)
counts=defaultdict(lambda:[0,0]);used=set()
for q in frames:
 for y in range(96):
  for x in range(96):
   i=q.getpixel((x,y));used.add(i)
   if i in rims:counts[i][int(protected(x,y))]+=1
free=iter(i for i in range(1,254) if i not in used and i>=235);roles=[];mapping={}
for i in rims:
 target,guard=counts[i];assert target
 # Exact rounded half of each5-bit RGB channel, without a color-space resize.
 before=tuple(v>>3 for v in original[3*i:3*i+3]);after=tuple((v+1)//2 for v in before);j=next(free) if guard else i
 pal[3*j:3*j+3]=bytes(v*255//31 for v in after);mapping[i]=j
 roles.append({'source_raw_index':i,'target_raw_index':j,'source_bgr5':list(before),'target_bgr5':list(after),'target_pixels':target,'protected_pixels':guard,'cloned':bool(guard)})
new=[];changed={}
for name,q in zip(names,frames):
 raw=[];n=0
 for y in range(96):
  for x in range(96):
   i=q.getpixel((x,y));j=mapping[i] if i in mapping and not protected(x,y) else i;raw.append(j)
   n+=i in mapping and not protected(x,y)
 out=Image.new('P',(96,96));out.putpalette([v for i in range(256) for v in pal[3*i:3*i+3][::-1]]);out.putdata(raw);out.info['transparency']=0;out.save(A/(name+'.png'),transparency=0);new.append(out);changed[name]=n
# Preserve original resource IDs, rectangles, dimensions and deduplication.
payloads={}
for pose,q in zip(base['poses'],new):
 for p in pose['parts']:
  data=bytes(q.getpixel((x,y)) if x<96 else 0 for y in range(p['y']+p['height']-1,p['y']-1,-1) for x in range(p['x'],p['x']+p['width']))
  rid=p['resource']
  if rid in payloads:assert payloads[rid]==data
  payloads[rid]=data
m=copy.deepcopy(base)
for rid,r in enumerate(m['resources']):
 before=(B/r['name']).read_bytes();assert len(before[786:])==len(payloads[rid]);(A/r['name']).write_bytes(before[:18]+bytes(pal)+payloads[rid]);r['sha256']=sha(A/r['name'])
(A/'palette.bgr24').write_bytes(pal)
delta=json.loads((B/'palette-delta.json').read_text());indices=[e['raw_index'] for e in delta['new_entries']]+[v['target_raw_index'] for v in roles if v['cloned']]
def word(i):
 b,g,r=[v>>3 for v in pal[3*i:3*i+3]];return 0x8000|r|(g<<5)|(b<<10)
delta['new_entries']=[{'raw_index':i,'rgb555':word(i)} for i in indices];(A/'palette-delta.json').write_text(json.dumps(delta,indent=2)+'\n')
m.update({'parent':'bf4e41df9c68511944176fa54f376e772a289b8f','base_manifest_sha256':sha(B/'manifest.json'),'lighting_roles':roles,'changed_pixels_per_frame':changed,'palette_added':len(indices),'palette_opaque_colors':len({word(i) for i in new[0].getdata() if i}),'palette_clone_slots':[v['target_raw_index'] for v in roles if v['cloned']],'source_frames_sha256':{n:sha(B/(n+'.png')) for n in names},'geometry_unchanged':True,'vdp1_delta':0,'cram_delta':0})
# Source guides belong to the immutable proportion milestone, not this color edit.
m.pop('source_sha256',None)
m['baseline_comparison_metrics']=m.pop('comparison_metrics')
(A/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(A/'rim-lighting-roles.json').write_text(json.dumps({'head_guard':'All pixels y<22','tie_guard':'49<=x<61 and22<=y<52','operation':'round-half each original5-bit BGR channel; no gamma/alpha/position changes','roles':roles,'future_use':'Offline roles for potential palette variants only; no runtime lighting engine.'},indent=2)+'\n')
for label,group,durations in [('idle',new[:3],[400,200,300]),('walk',new[3:],[120,120,120])]:
 ims=[q.resize((384,384),Image.Resampling.NEAREST) for q in group];ims[0].save(A/f'{label}-4x.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2,transparency=0)
new[0].convert('RGBA').save(A/'master-92-rgba.png');new[0].convert('RGBA').resize((768,768),Image.Resampling.NEAREST).save(A/'master-92-8x.png')
# All silhouettes at exact native size on one sole line; Buck is never rescaled.
line=Image.new('RGBA',(448,112),(27,31,43,255));d=ImageDraw.Draw(line)
for q,x,label in [(frames[0].convert('RGBA'),0,'BEFORE'),(new[0].convert('RGBA'),104,'SOFTER RIM'),(Image.open(R/'assets/animation-polish/buck-00.png').convert('RGBA'),208,'BUCK88'),(new[0].convert('RGBA'),352,'PUNK92')]:line.alpha_composite(q,(x,0));d.text((x+2,99),label,fill='white')
d.line((0,92,447,92),fill=(90,120,110));line.save(A/'comparison-native.png');line.resize((1792,448),Image.Resampling.NEAREST).save(A/'comparison-4x.png')
sheet=Image.new('RGBA',(576,112),(27,31,43,255));d=ImageDraw.Draw(sheet)
for i,(n,q) in enumerate(zip(names,new)):sheet.alpha_composite(q.convert('RGBA'),(96*i,0));d.text((96*i+2,99),n,fill='white')
sheet.save(A/'contact-native.png');sheet.resize((2304,448),Image.Resampling.NEAREST).save(A/'contact-4x.png')
print(json.dumps({'changed_pixels':changed,'palette_clone_slots':m['palette_clone_slots'],'texture_bytes':m['texture_bytes'],'boot_bytes':m['boot_bytes'],'boot_free':m['boot_free'],'boot_slots':m['boot_slots'],'new_master_colors':m['palette_opaque_colors']},indent=2))
