#!/usr/bin/env python3
"""Convert reviewed eight-pose guide into native shared-palette pieces.
No approved asset is regenerated. Binary alpha; fixed per-fighter scale, never
stretch passing poses to contact height. Native output is the review master.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from collections import deque
import json,struct,hashlib,math
R=Path(__file__).resolve().parents[1];O=R/'assets/running'
source=Image.open(O/'source/run-sheet.png').convert('RGBA');w,h=source.size
alpha=source.getchannel('A');raw=bytearray(1 if a>=128 else 0 for a in alpha.getdata());regions=[]
for start in range(w*h):
 if not raw[start]:continue
 raw[start]=0;q=deque([start]);pts=[]
 while q:
  p=q.popleft();pts.append(p)
  for n in (p-w,p+w,p-1 if p%w else -1,p+1 if p%w<w-1 else -1):
   if 0<=n<w*h and raw[n]:raw[n]=0;q.append(n)
 if len(pts)>50000:regions.append(pts)
assert len(regions)==8
regions.sort(key=lambda p:(min(p)//w//490,min(v%w for v in p)))
palette=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(palette[3*i:3*i+3][::-1]) for i in range(256)];memo={}
def quant(c):
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def png(a):
 im=Image.new('RGBA',(128,96));im.putdata([(*colors[i],255) if i else (0,0,0,0) for i in a]);return im
resources=[];pool={};actors=[];total=0;naive=0
for actor,name in enumerate(['buck','chuck']):
 group=regions[actor*4:actor*4+4];top=min(min(p)//w for p in group);bottom=max(max(p)//w for p in group)+1;scale=88/(bottom-top);frames=[]
 for f,pts in enumerate(group):
  left=min(p%w for p in pts);right=max(p%w for p in pts)+1;yt=min(p//w for p in pts);yb=max(p//w for p in pts)+1
  cell=Image.new('RGBA',(right-left,yb-yt));sp=source.load();cp=cell.load()
  for p in pts:cp[p%w-left,p//w-yt]=sp[p%w,p//w]
  # Constant source scale per fighter, then exact limited palette and binary alpha.
  cell=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
  native=Image.new('RGBA',(128,96));x=64-cell.width//2;y=4+round((yt-top)*scale)
  if f in (0,2):y=92-cell.height # two contact poses on the identical ground line
  native.alpha_composite(cell,(x,y));a=[quant(c[:3]) if c[3]>=128 else 0 for c in native.getdata()];im=png(a);im.save(O/f'{name}-{f}.png');parts=[]
  # Three disjoint bands, even-height rectangles for validated SGL registration.
  for lo,hi in [(0,28),(28,60),(60,96)]:
   box=im.crop((0,lo,128,hi)).getbbox();assert box
   x1,y1,x2,y2=box;y1+=lo;y2+=lo;y1=y1//2*2;y2=(y2+1)//2*2
   pw=math.ceil((x2-x1)/8)*8;ph=y2-y1;payload=bytes(a[yy*128+xx] if xx<128 else 0 for yy in range(y2-1,y1-1,-1) for xx in range(x1,x1+pw));key=(pw,ph,payload);size=(pw*ph+31)&~31;naive+=size
   if key not in pool:
    rid=len(resources);pool[key]=rid;fn=f'RN{rid:02}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,pw,ph);head[16]=8;blob=bytes(head)+palette+payload;(O/fn).write_bytes(blob);resources.append(dict(name=fn,width=pw,height=ph,bytes=size,sha256=hashlib.sha256(blob).hexdigest()));total+=size
   rid=pool[key];parts.append(dict(resource=rid+81,x=x1,y=y1,width=pw,height=ph))
  frames.append(dict(frame=f,phase=['near contact','far knee drive','far contact','near knee drive'][f],parts=parts,bounds=im.getbbox(),sha256=hashlib.sha256(im.tobytes()).hexdigest()))
 actors.append(dict(name=name,frames=frames,source_scale=scale));ims=[Image.open(O/f'{name}-{f}.png') for f in range(4)]
 for zoom in (1,4):
  sheet=Image.new('RGBA',(128*4,96));
  for f,im in enumerate(ims):sheet.alpha_composite(im,(128*f,0))
  sheet.resize((sheet.width*zoom,96*zoom),Image.Resampling.NEAREST).save(O/f'{name}-contact-{zoom}x.png')
  gs=[]
  for im in ims:
   q=Image.new('P',(128,96));q.putpalette([v for c in colors for v in c]);q.putdata([quant(c[:3]) if c[3] else 0 for c in im.getdata()]);q.info['transparency']=0;gs.append(q.resize((128*zoom,96*zoom),Image.Resampling.NEAREST))
  gs[0].save(O/f'{name}-run-{zoom}x.gif',save_all=True,append_images=gs[1:],duration=100,loop=0,transparency=0,disposal=2,optimize=False)
 # native walk/run side-by-side over their common24/30tick LCM120.
 gs=[]
 for t in range(0,120,2):
  im=Image.new('RGBA',(256,96));im.alpha_composite(Image.open(R/'assets/knee-lift'/f'{name}-{t//10%3:02}.png'),(0,0));im.alpha_composite(ims[t//6%4],(128,0));q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c]);q.putdata([quant(c[:3]) if c[3] else 0 for c in im.getdata()]);gs.append(q.resize((768,288),Image.Resampling.NEAREST))
 gs[0].save(O/f'{name}-walk-vs-run.gif',save_all=True,append_images=gs[1:],duration=[30,40,30]*20,loop=0,transparency=0,disposal=2,optimize=False)
manifest=dict(source_sha256=hashlib.sha256((O/'source/run-sheet.png').read_bytes()).hexdigest(),canvas=[128,96],root=[64,92],palette='assets/gallery/GB0.TGA',transparent_index=0,frame_ticks=6,unique_resources=len(resources),texture_bytes=total,naive_bytes=naive,dedup_saved=naive-total,boot_vdp1_bytes=362848+total,free_vdp1_bytes=95640-total,slots=135+len(resources),resources=resources,actors=actors)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
header='/* Generated by tools/build-running.py; shared gallery palette. */\n#ifndef MF_RUNNING_DATA_H\n#define MF_RUNNING_DATA_H\n#define MF_RUN_NEW %d\n#define MF_RUN_BYTES %du\nstatic const mf_polish_resource run_resources[MF_RUN_NEW]={\n'%(len(resources),total)
header+=',\n'.join('{"%s",%d,%d,%du}'%(r['name'],r['width'],r['height'],r['bytes']) for r in resources)+'};\nstatic const mf_polish_piece run_parts[2][4][3]={\n'
header+=',\n'.join('{'+','.join('{'+','.join('{%d,%d,%d,%d,%d}'%tuple(p[k] for k in ['resource','x','y','width','height']) for p in f['parts'])+'}' for f in a['frames'])+'}' for a in actors)+'};\n#endif\n'
(R/'src/running_data.h').write_text(header)
print(json.dumps({k:v for k,v in manifest.items() if k not in ['actors','resources']},indent=2))
