#!/usr/bin/env python3
"""Bounded key-pose prototype; generated guide is not a finished full moveset.
Lock existing head/feet pixels, convert to existing indexed palette, intern strips.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,struct,hashlib,math,sys
MOMENTUM="--momentum" in sys.argv
R=Path(__file__).resolve().parents[1];O=R/('assets/bat-momentum' if MOMENTUM else 'assets/combat-animation');O.mkdir(exist_ok=True)
for stale in O.glob('CA*.TGA'):stale.unlink()
pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786]
colors=[tuple(pal[3*i:3*i+3][::-1]) for i in range(256)];memo={}
def quant(c):
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def indexed(im):
 out=Image.new('RGBA',im.size);out.putdata([(*colors[quant(c[:3])],255) if c[3]>=160 else (0,0,0,0) for c in im.getdata()]);return out
source=Image.open(R/'assets/combat-animation/source/attack-keypose-guide.png').convert('RGBA');pool={};resources=[]
def piece(im,x,y):
 box=im.getbbox()
 if box is None:return None
 l,t,r,b=box;l=int(l);t=int(t);w=math.ceil((r-l)/8)*8;h=b-t
 # Even heights retain the same pinned SGL one-pixel registration as heroes.
 h+=(h%2);raw=[]
 for yy in range(t,t+h):
  for xx in range(l,l+w):
   c=im.getpixel((xx,yy)) if xx<im.width and yy<im.height else (0,0,0,0);raw.append(quant(c[:3]) if c[3] else 0)
 key=(w,h,bytes(raw))
 if key not in pool:
  rid=len(resources);pool[key]=rid;name=f'CA{rid:02}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,w,h);head[16]=8
  blob=bytes(head)+pal+b''.join(bytes(raw[q*w:(q+1)*w]) for q in range(h-1,-1,-1));(O/name).write_bytes(blob);resources.append(dict(name=name,width=w,height=h,bytes=(w*h+31)&~31,sha256=hashlib.sha256(blob).hexdigest()))
 return dict(resource=pool[key],x=x+l,y=y+t,width=w,height=h)
def pieces(im,start=0,end=112):
 v=[]
 for y in range(start,end,16):
  p=piece(im.crop((0,y,160,min(y+16,end))),0,y)
  if p:v.append(p)
 return v
frames=[];lower=[];preview=[]
for a,name in enumerate(['buck','chuck']):
 idle=Image.open(R/f'assets/animation-polish/{name}-00.png').convert('RGBA');poses=[]
 # The old lower crop accidentally retained a detached cuff/glove. Keep the
 # actual trouser/boot component, with every surviving native pixel unchanged.
 clean=idle.crop((0,48,128,96));remaining={(x,y) for y in range(48) for x in range(128) if clean.getpixel((x,y))[3]};components=[]
 while remaining:
  seed=remaining.pop();todo=[seed];component={seed}
  while todo:
   x,y=todo.pop()
   for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if q in remaining:remaining.remove(q);component.add(q);todo.append(q)
  components.append(component)
 keep=max(components,key=len)
 for c in components:
  if c is not keep:
   for q in c:clean.putpixel(q,(0,0,0,0))
 # Native body top20/ground108 == original top4/ground92 plus16.
 for f in range(4):
  top=0 if a==0 else 437;foot=434 if a==0 else 869
  # Common scale; only momentum contact gets an explicit20px waist registration.
  scale=88/(foot-(50 if a==0 else 482));cx=200+f*443.5-(20/scale if MOMENTUM and f==3 else 0);sy=(50 if a==0 else 482)
  native=source.transform((160,112),Image.Transform.AFFINE,(1/scale,0,cx-64/scale,0,1/scale,sy-20/scale),Image.Resampling.NEAREST)
  native=indexed(native)
  # Remove neighboring row/cell remnants; weapon and hands are confined to this cell.
  for y in range(112):
   for x in range(160):
    sx=cx+(x-64)/scale;yy=sy+(y-20)/scale
    if sx<f*443.5 or sx>=(f+1)*443.5 or yy<top or yy>foot:native.putpixel((x,y),(0,0,0,0))
  # Original exact head and native lower body; guide only supplies shoulders/arms/torso.
  # Head region excludes the carried weapon, located to the left in bat windup.
  for y in range(24):
   for x in range(128):
    if 39<=x<=88 and (f!=2 or x>=56 or idle.getpixel((x,y))[3]):native.putpixel((x,y+16),idle.getpixel((x,y)))
  native.paste((0,0,0,0),(0,64,160,112));native.alpha_composite(clean if MOMENTUM and f>=2 else idle.crop((0,48,128,96)),(0,64))
  native.save(O/f'{name}-key-{f}.png');poses.append(pieces(native,0,64))
 frames.append(poses)
 lows=[]
 for f in range(2 if MOMENTUM else 5):
  src=idle if f==0 or MOMENTUM else Image.open(R/f'assets/running/{name}-{f-1}.png').convert('RGBA')
  low=Image.new('RGBA',(160,112));low.alpha_composite(clean if MOMENTUM and f==1 else src.crop((0,48,128,96)),(0,64));lows.append(pieces(low,64,112))
 lower.append(lows)
 # Honest key-pose preview: only two authored attack keys, with neutral recovery.
 neutral=Image.new('RGBA',(160,112));neutral.alpha_composite(idle,(0,16))
 for kind,keys,ticks in [('punch',[None,0,1,0,None],[2,3,5,5,9]),('bat',[2,2,3,3,2],[5,6,6,10,9])]:
  ims=[neutral if k is None else Image.open(O/f'{name}-key-{k}.png') for k in keys]
  for z in [1,4]:
   canv=[]
   for im in ims:
    p=Image.new('RGBA',im.size,(16,20,32,255));p.alpha_composite(im);canv.append(p.resize((160*z,112*z),Image.Resampling.NEAREST))
   canv[0].save(O/f'{name}-{kind}-{z}x.gif',save_all=True,append_images=canv[1:],duration=[round(v*1000/60) for v in ticks],loop=0,disposal=2)
 sheet=Image.new('RGBA',(800,128),(16,20,32,255));d=ImageDraw.Draw(sheet)
 for f in range(5):
  im=neutral if f==0 else Image.open(O/f'{name}-key-{f-1}.png');sheet.alpha_composite(im,(f*160,0));d.text((f*160+3,114),['APPROVED IDLE','PUNCH CHAMBER','PUNCH EXTEND','BAT WINDUP','BAT CONTACT'][f],fill='white')
 sheet.save(O/f'{name}-contact-native.png');sheet.resize((3200,512),Image.Resampling.NEAREST).save(O/f'{name}-contact-4x.png')
# Moving swing preview uses the exact old alternating lower-body pixels.
for a,name in enumerate(['buck','chuck']):
 seq=[];times=[];previous=None
 for tick in range(1,37):
  if tick<6 and not MOMENTUM:
   im=Image.new('RGBA',(160,112));im.alpha_composite(Image.open(R/f'assets/running-bat-visual/{name}-run-0.png'),(0,16))
  else:
   key=2 if tick<12 or tick>=28 else 3;phase=((tick-6)//6)%4
   im=Image.new('RGBA',(160,112));im.alpha_composite(Image.open(O/f'{name}-key-{key}.png').crop((0,0,160,64)));im.alpha_composite((Image.open(O/f'{name}-key-{key}.png').crop((0,64,128,112)) if MOMENTUM else Image.open(R/f'assets/running/{name}-{phase}.png').crop((0,48,128,96))),(0,64))
  raw=im.tobytes()
  if raw==previous:times[-1]+=1
  else:seq.append(im);times.append(1);previous=raw
 for z in [1,4]:
  ims=[]
  for im in seq:
   bg=Image.new('RGBA',im.size,(16,20,32,255));bg.alpha_composite(im);ims.append(bg.resize((160*z,112*z),Image.Resampling.NEAREST))
  ims[0].save(O/f'{name}-running-swing-{z}x.gif',save_all=True,append_images=ims[1:],duration=[round(v*1000/60) for v in times],loop=0,disposal=2)
total=sum(p['bytes'] for p in resources);m=dict(parent=('176ba47494a7d539904fce490e65d138b9358f3e' if MOMENTUM else '20b0fcf743ace0e16f74cb3dcdf22fd93dd8ead9'),quality='limited two-key prototype per attack; NOT full-quality finished animation',canvas=[160,112],root=[64,108],head_lock=[39,0,89,24],upper_end=48,palette='assets/gallery/GB0.TGA',resources=resources,frames=frames,lowers=lower,texture_bytes=total,boot_bytes=410464+total,free_bytes=48024-total,slots=169+len(resources));
if MOMENTUM:m.update(momentum=True,registration_dx=[[0,0,0,20],[0,0,0,20]])
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
assert m['free_bytes']>=0,m
# Variable piece lists terminate with resource -1; head/body/weapon strips interned once.
def arr(v):return '{'+','.join('{%d,%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width'],p['height']) for p in v)+',{-1,0,0,0,0}}'
maxupper=max(len(v) for actor in frames for v in actor)+1;maxlower=max(len(v) for actor in lower for v in actor)+1
h='#ifndef MF_COMBAT_ANIMATION_DATA_H\n#define MF_COMBAT_ANIMATION_DATA_H\n#define MF_CA_NEW %d\n#define MF_CA_BYTES %du\n'%(len(resources),total)
h+='static const mf_polish_resource ca_resources[MF_CA_NEW]={'+','.join('{"%s",%d,%d,%du}'%(p['name'],p['width'],p['height'],p['bytes']) for p in resources)+'};\n'
h+='static const mf_polish_piece ca_upper[2][4][%d]={'%maxupper+','.join('{'+','.join(arr(v) for v in actor)+'}' for actor in frames)+'};\n'
h+='static const mf_polish_piece ca_lower[2][%d][%d]={'%((2 if MOMENTUM else 5),maxlower)+','.join('{'+','.join(arr(v) for v in actor)+'}' for actor in lower)+'};\n#endif\n';(R/('src/bat_momentum_data.h' if MOMENTUM else 'src/combat_animation_data.h')).write_text(h)
print(f'Limited combat prototype: {len(resources)} shared strips, {total} extra bytes; {m["boot_bytes"]} allocated/{m["free_bytes"]} free; {m["slots"]} textures')
