#!/usr/bin/env python3
"""Compose actual near/far leg layers two phases apart; lock approved upper art.
The original guide/generator remains archived. This script is the corrected
native master's reproducible authoring path, not a gameplay transformation.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from collections import deque
import json,hashlib,struct,math
R=Path(__file__).resolve().parents[1];O=R/'assets/running';D=R/'assets/stride-fix';B=D/'before';LOCK=48
source=Image.open(D/'source/single-leg-guide.png').convert('RGBA');w,h=source.size;raw=bytearray(a>=128 for a in source.getchannel('A').getdata());regions=[]
for start in range(w*h):
 if not raw[start]:continue
 raw[start]=0;q=deque([start]);pts=[]
 while q:
  p=q.popleft();pts.append(p)
  for n in (p-w,p+w,p-1 if p%w else -1,p+1 if p%w<w-1 else -1):
   if 0<=n<w*h and raw[n]:raw[n]=0;q.append(n)
 if len(pts)>20000:regions.append(pts)
assert len(regions)==8
regions.sort(key=lambda pts:(min(pts)//w//440,min(p%w for p in pts)))
palette=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(palette[3*i:3*i+3][::-1]) for i in range(256)];memo={}
def quant(c):
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def indexed(im):return [quant(c[:3]) if c[3]>=128 else 0 for c in im.getdata()]
def png(a):
 im=Image.new('RGBA',(128,96));im.putdata([(*colors[i],255) if i else (0,0,0,0) for i in a]);return im
resources=[];pool={};actors=[];total=0;naive=0;identical=[]
for n in O.glob('RN*.TGA'):n.unlink()
for ai,name in enumerate(['buck','chuck']):
 layers=[];meta=[]
 for phase,pts in enumerate(regions[ai*4:ai*4+4]):
  x1=min(p%w for p in pts);x2=max(p%w for p in pts)+1;y1=min(p//w for p in pts);y2=max(p//w for p in pts)+1
  # Locate the top hip edge itself, not the center of a backward-reaching boot.
  hipxs=[p%w for p in pts if p//w<=y1+3];hx=round((min(hipxs)+max(hipxs))/2)
  cell=Image.new('RGBA',(x2-x1,y2-y1));sp=source.load();cp=cell.load()
  for p in pts:cp[p%w-x1,p//w-y1]=sp[p%w,p//w]
  # Source anatomical projections: contact48px, trailing46px, passing phases
  # use the contact's constant scale; no stretching bent knees to the floor.
  contact_pts=regions[ai*4];contact_h=max(contact_pts)//w-min(contact_pts)//w+1;scale=48/contact_h
  nh=46 if phase==2 else round(cell.height*scale);nw=round(cell.width*scale)
  cell=cell.resize((nw,nh),Image.Resampling.NEAREST)
  layer=Image.new('RGBA',(128,96));px=64-round((hx-x1)*scale);layer.alpha_composite(cell,(px,44));layer=png(indexed(layer));layer.save(D/f'{name}-leg-{phase}.png');layers.append(layer)
  meta.append(dict(phase=phase,source_bounds=[x1,y1,x2,y2],source_hip=[hx,y1],native_hip=[64,44],native_size=[nw,nh],sha256=hashlib.sha256(layer.tobytes()).hexdigest()))
 frames=[];ims=[];diagrams=[]
 for f in range(4):
  old=Image.open(B/f'{name}-{f}.png').convert('RGBA');near_phase=[0,2,1,3][f];far_phase=[1,3,0,2][f]
  # Two persistent anatomical legs. Their phase offset and compositing order
  # remain fixed; full-chain geometry moves, not just reused boots.
  far=layers[far_phase].copy();far.putdata([(*colors[quant(tuple(round(v*.83) for v in c[:3]))],255) if c[3] else (0,0,0,0) for c in far.getdata()])
  far_shift=Image.new('RGBA',(128,96));far_shift.alpha_composite(far,(-2,0));near=Image.new('RGBA',(128,96));near.alpha_composite(layers[near_phase],(2,0));im=Image.new('RGBA',(128,96));im.alpha_composite(far_shift);im.alpha_composite(near)
  # Preserve the approved upper art, excluding explicit stale-leg repair mattes.
  leg_underlay=im.copy();im.paste(old.crop((0,0,128,LOCK)),(0,0))
  repair=R/'assets/leg-artifact-fix'/f'{name}-{f}-mask.png'
  repair_mask=Image.open(repair).convert('L') if repair.exists() else Image.new('L',(128,96))
  im.paste(leg_underlay,(0,0),repair_mask)
  a=indexed(im);im=png(a)
  for yy in range(LOCK):
   for xx in range(128):
    if not repair_mask.getpixel((xx,yy)):assert im.getpixel((xx,yy))==old.getpixel((xx,yy))
  im.save(O/f'{name}-{f}.png');ims.append(im)
  parts=[]
  def cost(cut):
   result=0
   for lo,hi in [(28,cut),(cut,96)]:
    box=im.crop((0,lo,128,hi)).getbbox()
    if box is None:return 10**9
    x1,y1,x2,y2=box;y1+=lo;y2+=lo;y1=y1//2*2;y2=(y2+1)//2*2;pw=math.ceil((x2-x1)/8)*8
    result+=(pw*(y2-y1)+31)&~31
   return result
  cut=min(range(52,83,2),key=lambda cut:(cost(cut),abs(cut-60)))
  for lo,hi in [(0,28),(28,cut),(cut,96)]:
   box=im.crop((0,lo,128,hi)).getbbox();assert box;x1,y1,x2,y2=box;y1+=lo;y2+=lo;y1=y1//2*2;y2=(y2+1)//2*2;pw=math.ceil((x2-x1)/8)*8;ph=y2-y1
   payload=bytes(a[yy*128+xx] if xx<128 else 0 for yy in range(y2-1,y1-1,-1) for xx in range(x1,x1+pw));key=(pw,ph,payload);size=(pw*ph+31)&~31;naive+=size
   if key not in pool:
    rid=len(resources);pool[key]=rid;fn=f'RN{rid:02}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,pw,ph);head[16]=8;blob=bytes(head)+palette+payload;(O/fn).write_bytes(blob);resources.append(dict(name=fn,width=pw,height=ph,bytes=size,sha256=hashlib.sha256(blob).hexdigest()));total+=size
    if (B/fn).exists() and (B/fn).read_bytes()==blob:identical.append(fn)
   parts.append(dict(resource=pool[key]+81,x=x1,y=y1,width=pw,height=ph))
  frame=dict(frame=f,phase=['near leads / far trails','near push-off / far drives','far leads / near recovery','far push-off / near drives'][f],near_phase=near_phase,far_phase=far_phase,leading_leg=['near','far','far','near'][f],parts=parts,bounds=im.getbbox(),sha256=hashlib.sha256(im.tobytes()).hexdigest());frames.append(frame)
  # Development diagram: color the actual layer coverage before occlusion so
  # both legs can be followed, never used as palette indices in shipped TGAs.
  diagram=im.copy();overlay=Image.new('RGBA',(128,96))
  for leg,col in [(far_shift,(32,210,255,160)),(near,(255,92,80,160))]:
   tint=Image.new('RGBA',(128,96));tint.putdata([col if c[3] and y>=LOCK else (0,0,0,0) for y in range(96) for c in [leg.getpixel((x,y)) for x in range(128)] ]);overlay.alpha_composite(tint)
  diagram.alpha_composite(overlay);diagrams.append(diagram)
 actors.append(dict(name=name,frames=frames,leg_layers=meta));
 for zoom in (1,4):
  sheet=Image.new('RGBA',(512,96))
  for f,im in enumerate(ims):sheet.alpha_composite(im,(128*f,0))
  sheet.resize((512*zoom,96*zoom),Image.Resampling.NEAREST).save(O/f'{name}-contact-{zoom}x.png')
  gifs=[]
  for im in ims:
   q=Image.new('P',(128,96));q.putpalette([v for c in colors for v in c]);q.putdata(indexed(im));q.info['transparency']=0;gifs.append(q.resize((128*zoom,96*zoom),Image.Resampling.NEAREST))
  gifs[0].save(O/f'{name}-run-{zoom}x.gif',save_all=True,append_images=gifs[1:],duration=100,loop=0,transparency=0,disposal=2,optimize=False)
 # Simultaneous before/after at identical6-tick holds; no re-timing to hide gait.
 gifs=[]
 for f,im in enumerate(ims):
  q=Image.new('RGBA',(256,96));q.alpha_composite(Image.open(B/f'{name}-{f}.png'),(0,0));q.alpha_composite(im,(128,0));gifs.append(q.resize((1024,384),Image.Resampling.NEAREST))
 gifs[0].save(D/f'{name}-before-after.gif',save_all=True,append_images=gifs[1:],duration=100,loop=0,disposal=2)
 sheet=Image.new('RGBA',(512,116),(12,18,30,255));draw=ImageDraw.Draw(sheet)
 for f,im in enumerate(diagrams):
  sheet.alpha_composite(im,(128*f,0));draw.text((128*f+3,96),f'{f+1} '+['NEAR CONTACT','FAR DRIVE','FAR CONTACT','NEAR DRIVE'][f],fill='white')
 draw.text((3,106),'RED: near/right  CYAN: far/left. Always same identity.',fill='white');sheet.resize((2048,464),Image.Resampling.NEAREST).save(D/f'{name}-identity-4x.png')
 # Update walk/run comparison with unchanged approved walking source.
 gifs=[]
 for t in range(0,120,2):
  im=Image.new('RGBA',(256,96));im.alpha_composite(Image.open(R/'assets/knee-lift'/f'{name}-{t//10%3:02}.png'),(0,0));im.alpha_composite(ims[t//6%4],(128,0));q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c]);q.putdata([quant(c[:3]) if c[3] else 0 for c in im.getdata()]);gifs.append(q.resize((768,288),Image.Resampling.NEAREST))
 gifs[0].save(O/f'{name}-walk-vs-run.gif',save_all=True,append_images=gifs[1:],duration=[30,40,30]*20,loop=0,transparency=0,disposal=2,optimize=False)
old=json.loads((B/'manifest.json').read_text());manifest={k:v for k,v in old.items() if k not in ['actors','resources','source_scale']};manifest.update(actors=actors,resources=resources,texture_bytes=total,naive_bytes=naive,dedup_saved=naive-total,unique_resources=len(resources),boot_vdp1_bytes=362848+total,free_vdp1_bytes=95640-total,slots=135+len(resources),stride_correction=dict(parent='05f2a58f42c5246bbf46e41ebacdba78d0e3b8f3',guide_sha256=hashlib.sha256((D/'source/single-leg-guide.png').read_bytes()).hexdigest(),upper_lock_rows=LOCK,reused_identical_pieces=identical,near_phases=[0,2,1,3],far_phases=[1,3,0,2]))
repair_dir=R/'assets/leg-artifact-fix'
manifest['artifact_correction']=dict(parent='aae373fb6fe1b7d0ca63210a071a8bb85ad500c8',reference_sha256=hashlib.sha256((repair_dir/'source/cleanup-reference.png').read_bytes()).hexdigest(),masks={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(repair_dir.glob('*-mask.png'))},unchanged_frames=[0,2],edit_bounds=[54,43,90,48])
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
header='/* Generated by tools/fix-running-stride.py; approved upper art locked. */\n#ifndef MF_RUNNING_DATA_H\n#define MF_RUNNING_DATA_H\n#define MF_RUN_NEW %d\n#define MF_RUN_BYTES %du\nstatic const mf_polish_resource run_resources[MF_RUN_NEW]={\n'%(len(resources),total)
header+=',\n'.join('{"%s",%d,%d,%du}'%(r['name'],r['width'],r['height'],r['bytes']) for r in resources)+'};\nstatic const mf_polish_piece run_parts[2][4][3]={\n'
header+=',\n'.join('{'+','.join('{'+','.join('{%d,%d,%d,%d,%d}'%tuple(p[k] for k in ['resource','x','y','width','height']) for p in f['parts'])+'}' for f in a['frames'])+'}' for a in actors)+'};\n#endif\n';(R/'src/running_data.h').write_text(header)
assert total<=old['texture_bytes'],(total,old['texture_bytes'])
print('Stride textures',total,'delta',total-old['texture_bytes'],'free',95640-total,'identical reused',identical)

# Combined two-fighter review sheet, exact native scale and shared ground rows.
for zoom in [1,4]:
 sheet=Image.new('RGBA',(512,192))
 for i,name in enumerate(['buck','chuck']):sheet.alpha_composite(Image.open(O/f'{name}-contact-1x.png'),(0,i*96))
 sheet.resize((512*zoom,192*zoom),Image.Resampling.NEAREST).save(D/('contact-native.png' if zoom==1 else 'contact-4x.png'))
