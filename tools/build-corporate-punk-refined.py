#!/usr/bin/env python3
"""Offline native reconstruction imports and globally deduplicated Saturn bank.
No old sprite is stretched. Nearest-neighbor is used only for review enlargements.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import json,struct,hashlib,itertools
R=Path(__file__).resolve().parents[1];A=R/'assets/corporate-punk-refined';A.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def isolate(q):
 q=q.convert('RGBA');q.putalpha(q.getchannel('A').point(lambda v:255 if v>=192 else 0));return q.crop(q.getbbox())
def raster(q,w,h,dark_fraction=.30,highlight=False):
 """Coverage/cluster-median import, preserving hard contours, not soft filtering."""
 a=np.asarray(q);out=Image.new('RGBA',(w,h))
 for y in range(h):
  for x in range(w):
   b=a[y*q.height//h:max(y*q.height//h+1,(y+1)*q.height//h),x*q.width//w:max(x*q.width//w+1,(x+1)*q.width//w)].reshape(-1,4);v=b[b[:,3]>=192]
   if len(v)<len(b)*.25:continue
   dark=v[v[:,:3].astype(int).sum(axis=1)<150];bright=v[v[:,:3].min(axis=1)>195]
   if highlight and len(bright)>=len(v)*.075 and len(dark)>=len(v)*.3:v=bright
   elif len(dark)>=len(v)*dark_fraction:v=dark
   out.putpixel((x,y),(*map(int,np.median(v[:,:3],axis=0)),255))
 return out
# 88 and92 are separate model-authored proportion studies, not stretched84px art.
g=Image.open(A/'source/master-candidate-guide.png').convert('RGBA');candidates=[]
for i,h in enumerate([88,92]):
 q=isolate(g.crop((i*g.width//2,0,(i+1)*g.width//2,g.height)));w=round(q.width*h/q.height);v=Image.new('RGBA',(96,96));v.alpha_composite(raster(q,w,h),(48-w//2,92-h));candidates.append(v)
# Dedicated finer native cluster reconstruction for the selected92px body.
q=isolate(Image.open(A/'source/native-cluster-cleanup-guide.png'));w=round(q.width*92/q.height);candidates[1]=Image.new('RGBA',(96,96));candidates[1].alpha_composite(raster(q,w,92),(48-w//2,0))
# Decode the deliberately enlarged24x28 head grid, preserving tiny eye highlights.
head=raster(Image.open(A/'source/native-head-grid-guide.png').convert('RGBA'),24,28,.23,True)
for h,q in zip([88,92],candidates):q.paste(head,(48,92-h))
master=candidates[1];guide=Image.open(A/'source/animation-refinement-guide.png').convert('RGBA')
def registered(cell):
 q=isolate(guide.crop((cell*guide.width//5,0,(cell+1)*guide.width//5,guide.height)));w=round(q.width*92/q.height);q=raster(q,w,92)
 # Register the pelvis, not the moving foot or total bounding-box center.
 pts=[x for y in range(44,51) for x in range(w) if q.getpixel((x,y))[3]]
 ref=[x for y in range(44,51) for x in range(96) if master.getpixel((x,y))[3]]
 left=round(sum(ref)/len(ref)-sum(pts)/len(pts));out=Image.new('RGBA',(96,96));out.alpha_composite(q,(left,0))
 seen=set()
 for yy in range(96):
  for xx in range(96):
   if (xx,yy) in seen or not out.getpixel((xx,yy))[3]:continue
   todo=[(xx,yy)];seen.add((xx,yy));part=[]
   while todo:
    px,py=todo.pop();part.append((px,py))
    for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
     if 0<=nx<96 and 0<=ny<96 and (nx,ny) not in seen and out.getpixel((nx,ny))[3]:seen.add((nx,ny));todo.append((nx,ny))
   if len(part)<=4:
    for point in part:out.putpixel(point,(0,0,0,0))
 return out
frames=[master.copy()]
# Local idle patches only; full head/face/mohawk, pelvis and planted feet locked.
for cell in [0,1]:
 q=master.copy();v=registered(cell)
 for x0,y0,x1,y1 in [(29,22,42,33),(66,27,77,39)]:
  for y in range(y0,y1):
   for x in range(x0,x1):
    if q.getpixel((x,y))[3] and v.getpixel((x,y))[3]:q.putpixel((x,y),v.getpixel((x,y)))
 frames.append(q)
for cell in [2,None,4]:
 q=master.copy()
 if cell is not None:q.paste(registered(cell).crop((0,52,96,92)),(0,52))
 frames.append(q)
print('Pre-quant native RGB555 colors',len({(p[0]>>3)|((p[1]>>3)<<5)|((p[2]>>3)<<10) for p in master.getdata() if p[3]}))
master.save(A/'source/native-master-reference.png')
# One shared no-dither palette: legacy raw0..14 preserved, new unused slots only.
swatch=Image.new('RGB',(sum(sum(p[3]>0 for p in q.getdata()) for q in frames+candidates),1));swatch.putdata([tuple((c>>3)*8 for c in p[:3]) for q in frames+candidates for p in q.getdata() if p[3]])
quant=swatch.quantize(colors=224,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);qp=quant.getpalette()
def word(c):return (c[0]>>3)|((c[1]>>3)<<5)|((c[2]>>3)<<10)
def rgb(v):return tuple(((v>>s)&31)*255//31 for s in [0,5,10])
words=sorted({word(qp[3*i:3*i+3]) for i in set(quant.getdata())});legacy=(R/'assets/cd/EN00.TGA').read_bytes();pal=bytearray(legacy[18:786]);oldused=set()
for p in (R/'assets/cd').glob('EN*.TGA'):oldused.update(p.read_bytes()[786:])
lookup={word(pal[3*i:3*i+3][::-1]):i for i in oldused if i};free=iter(i for i in range(1,254) if i not in oldused);added=[]
for v in words:
 if v not in lookup:
  i=next(free);lookup[v]=i;pal[3*i:3*i+3]=bytes(rgb(v)[::-1]);added.append({'raw_index':i,'rgb555':0x8000|v})
colors=[rgb(v) for v in words];memo={}
def index(q):
 def nearest(p):
  if not p[3]:return 0
  c=p[:3]
  if c not in memo:memo[c]=lookup[words[min(range(len(words)),key=lambda j:sum((c[k]-colors[j][k])**2 for k in range(3)))]]
  return memo[c]
 im=Image.new('P',(96,96));im.putpalette([v for i in range(256) for v in pal[3*i:3*i+3][::-1]]);im.putdata([nearest(p) for p in q.getdata()]);im.info['transparency']=0;return im
frames=list(map(index,frames));candidates=list(map(index,candidates));names=['idle-0','idle-1','idle-2','walk-0','walk-1','walk-2']
for n,q in zip(names,frames):q.save(A/(n+'.png'),transparency=0)
for h,q in zip([88,92],candidates):q.save(A/f'candidate-{h}.png',transparency=0)
for old in A.glob('CP*.TGA'):old.unlink()
def pack(cuts,write=False):
 resources=[];poses=[];lookup={}
 for n,q in zip(names,frames):
  rgba=q.convert('RGBA');raw=bytes(q.getdata());parts=[]
  for top,bottom in zip(cuts,cuts[1:]):
   box=rgba.crop((0,top,96,bottom)).getbbox();x,y,x2,y2=box;y+=top;y2+=top
   # Keep band edges fixed to avoid overlap and keep even raster dimensions.
   y=top;y2=bottom;w=(x2-x+7)//8*8;h=y2-y;payload=bytes(raw[yy*96+xx] if xx<96 else 0 for yy in range(y2-1,y-1,-1) for xx in range(x,x+w));key=(w,h,payload)
   if key not in lookup:
    rid=len(resources);lookup[key]=rid;filename=f'CP{rid:02d}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,w,h);head[16]=8;data=bytes(head)+bytes(pal)+payload
    if write:(A/filename).write_bytes(data)
    resources.append({'name':filename,'width':w,'height':h,'bytes':(w*h+31)&~31,'sha256':hashlib.sha256(data).hexdigest()})
   parts.append({'resource':lookup[key],'x':x,'y':y,'width':w,'height':h})
  poses.append({'name':n,'parts':parts})
 return sum(r['bytes'] for r in resources),resources,poses
# Evaluate shared-bank costs, including reuse of unchanged upper body/feet.
layouts=[]
for cuts in [(0,26,76,92),(0,26,52,92),(0,26,52,76,92),(0,22,52,76,92),(0,26,52,68,92),(0,26,52,68,80,92)]:
 cost,res,poses=pack(cuts);layouts.append({'cuts':list(cuts),'bytes':cost,'resources':len(res),'pieces_per_pose':len(cuts)-1})
minimum=min(v['bytes'] for v in layouts);chosen=min((v for v in layouts if v['bytes']<=minimum*1.08),key=lambda v:(v['pieces_per_pose'],v['bytes']));cost,res,poses=pack(chosen['cuts'],True)
(A/'palette.bgr24').write_bytes(pal);(A/'palette-delta.json').write_text(json.dumps({'legacy_indices':sorted(oldused),'new_entries':added},indent=2)+'\n')
for label,group,durations in [('idle',frames[:3],[400,200,300]),('walk',frames[3:],[120,120,120])]:
 ims=[q.resize((384,384),Image.Resampling.NEAREST) for q in group];ims[0].save(A/f'{label}-4x.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2,transparency=0)
master_rgba=frames[0].convert('RGBA');master_rgba.save(A/'master-92-rgba.png');master_rgba.resize((768,768),Image.Resampling.NEAREST).save(A/'master-92-8x.png')
line=Image.new('RGBA',(640,112),(27,31,43,255));d=ImageDraw.Draw(line)
line_actors=[('Buck88',Image.open(R/'assets/animation-polish/buck-00.png').convert('RGBA'),0),('Chuck88',Image.open(R/'assets/animation-polish/chuck-00.png').convert('RGBA'),128),('Old84',Image.open(R/'assets/corporate-punk-animation/idle-0.png').convert('RGBA'),272),('New88',candidates[0].convert('RGBA'),400),('New92',master_rgba,528)]
for label,q,x in line_actors:line.alpha_composite(q,(x,0));d.text((x+2,99),label,fill='white')
d.line((0,92,639,92),fill=(90,120,110));line.save(A/'lineup-native.png');line.resize((2560,448),Image.Resampling.NEAREST).save(A/'lineup-4x.png')
sheet=Image.new('RGBA',(576,112),(27,31,43,255));d=ImageDraw.Draw(sheet)
for i,(n,q) in enumerate(zip(names,frames)):sheet.alpha_composite(q.convert('RGBA'),(i*96,0));d.text((i*96+2,99),n,fill='white')
sheet.save(A/'contact-native.png');sheet.resize((2304,448),Image.Resampling.NEAREST).save(A/'contact-4x.png')
metrics={}
for label,q,x in line_actors:
 a=np.asarray(q);opaque=a[:,:,3]>0;v=(a[:,:,:3]//8);same=(v[:,:-1]==v[:,1:]).all(axis=2);pairs=opaque[:,:-1]&opaque[:,1:];b=q.getbbox();metrics[label]={'bounds':list(b),'width':b[2]-b[0],'height':b[3]-b[1],'opaque_rgb555_colors':len({word(p[:3]) for p in q.getdata() if p[3]}),'same_color_horizontal_pair_fraction':round(float(same[pairs].mean()),4)}
m={'parent':'f45cad4b4d4fdf56e9030997c7536df714866ef6','canvas':[96,96],'root':[48,92],'selected_height':92,'opaque_bounds':list(master_rgba.getbbox()),'palette_added':len(added),'palette_opaque_colors':len(set(frames[0].getdata())-{0}),'resources':res,'poses':poses,'texture_bytes':cost,'texture_slots':len(res),'pieces_per_pose':len(chosen['cuts'])-1,'layout_candidates':layouts,'selected_cuts':chosen['cuts'],'idle_holds':[24,12,18],'walk_holds':[7,7,7],'boot_bytes':351104+cost,'boot_free':458488-351104-cost,'full_bytes':427104+cost,'full_free':458488-427104-cost,'boot_slots':125+len(res),'full_slots':176+len(res),'comparison_metrics':metrics,'source_sha256':{p.name:sha(p) for p in sorted((A/'source').glob('*.png'))}}
(A/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
h=['/* Offline-generated fine-detail92px enemy bank. */','#ifndef MF_CORPORATE_REFINED_DATA_H','#define MF_CORPORATE_REFINED_DATA_H',f'#define MF_CP_TEXTURE_BYTES {cost}u',f'#define MF_CP_RESOURCES {len(res)}',f'#define MF_CP_PARTS {m["pieces_per_pose"]}','typedef struct {const char *name;short width,height;} mf_cp_resource;','typedef struct {short resource,x,y,width;} mf_cp_piece;','static const mf_cp_resource cp_resources[]={']
h+=[' {"%s",%d,%d},'%(r['name'],r['width'],r['height']) for r in res];h+=['};',f'static const mf_cp_piece cp_poses[6][MF_CP_PARTS]={{'];h+=[' {'+','.join('{%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width']) for p in pose['parts'])+'},' for pose in poses];h+=['};','#endif'];(R/'src/corporate_refined_data.h').write_text('\n'.join(h)+'\n')
print(json.dumps({k:m[k] for k in ['opaque_bounds','palette_added','palette_opaque_colors','texture_bytes','texture_slots','pieces_per_pose','boot_bytes','boot_free','full_free','boot_slots','layout_candidates']},indent=2))
