#!/usr/bin/env python3
"""Shared native carry weapon and exact wood-pixel metal covers for running bat.
No hero/enemy source frame, palette, leg geometry or combat artwork is rewritten.
"""
from pathlib import Path
from PIL import Image
import json,hashlib,struct,math
R=Path(__file__).resolve().parents[1];O=R/'assets/running-bat-visual';O.mkdir(exist_ok=True)
pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(pal[3*i:3*i+3][::-1]) for i in range(256)];memo={}
def quant(c):
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def rgba(a,w,h):
 im=Image.new('RGBA',(w,h));im.putdata([(*colors[i],255) if i else (0,0,0,0) for i in a]);return im
pool={};res=[];total=0
for stale in O.glob('RBV*.TGA'):stale.unlink()
def export(im,parity=0):
 global total
 box=im.getbbox();assert box;x,y,x2,y2=box;w=math.ceil((x2-x)/8)*8;h=y2-y
 if h%2!=parity:h+=1
 a=[quant(im.getpixel((xx,yy))[:3]) if xx<im.width and yy<im.height and im.getpixel((xx,yy))[3]>=128 else 0 for yy in range(y,y+h) for xx in range(x,x+w)]
 raw=bytes(a[yy*w+xx] for yy in range(h-1,-1,-1) for xx in range(w));key=(w,h,raw)
 if key not in pool:
  i=len(res);pool[key]=i;name=f'RBV{i:02}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,w,h);head[16]=8;blob=bytes(head)+pal+raw;(O/name).write_bytes(blob);size=(w*h+31)&~31;total+=size;res.append(dict(name=name,width=w,height=h,bytes=size,sha256=hashlib.sha256(blob).hexdigest()))
 return dict(resource=pool[key],x=x,y=y,width=w,height=h)
# One isolated weapon guide, not the concept's bodies/legs. Final alpha/index
# boundaries are binary native pixels and mapped to the existing cool-metal ramp.
source=Image.open(O/'source/aluminum-bat-guide.png').convert('RGBA');mask=source.getchannel('A').point(lambda v:255 if v>=128 else 0);box=mask.getbbox();cell=source.crop(box).resize((27,36),Image.Resampling.NEAREST);carry=Image.new('RGBA',(32,40));carry.alpha_composite(cell,(2,2));carry=rgba([quant(c[:3]) if c[3]>=128 else 0 for c in carry.getdata()],32,40);carry.save(O/'carry-native.png');carry.resize((256,320),Image.Resampling.NEAREST).save(O/'carry-8x.png');cp=export(carry);cp['grip']=[24-cp['x'],32-cp['y']]
hands=[[[43,43],[41,37],[43,43],[37,40]],[[39,43],[41,41],[39,37],[40,40]]]
# Legacy bat wood colors are unique authoring colors. Exact visible-pixel masks
# preserve hands, body pixels, occlusion, and original swing geometry per actor.
wood={(184,136,80):(144,152,176),(224,184,120):(232,232,240),(128,96,56):(72,80,104),(208,160,104):(192,200,216)}
meta=json.loads((R/'assets/bat-frames.json').read_text());overlays=[]
# Derive true surviving weapon pixels from the original authoring function,
# replacing only its four literal wood paint colors with sentinel colors.
# This excludes coincidentally equal hair/skin/buckle colors elsewhere.
import sys
sys.path.insert(0,str(R/'tools'))
from buck_art import draw_buck
sentinels={(255,0,254),(254,0,253),(253,0,252),(252,0,251)}
author=(R/'tools/buck_art.py').read_text()
for old,new in zip(['#b88850','#e0b878','#806038','#d0a068'],['#ff00fe','#fe00fd','#fd00fc','#fc00fb']):author=author.replace("'"+old+"'","'"+new+"'")
ns={};exec(compile(author,'weapon-mask-authoring','exec'),ns)

for actor in ['buck','chuck']:
 poses=[]
 for f,m in enumerate(meta[actor]):
  authored=draw_buck(15+f,chuck=actor=='chuck');assert hashlib.sha256(authored.tobytes()).hexdigest()==m['source_rgb_sha256']
  marked=ns['draw_buck'](15+f,chuck=actor=='chuck')
  blob=(R/'assets/cd'/m['name']).read_bytes();w,h=struct.unpack_from('<HH',blob,12);p=blob[18:786];raw=blob[786:];im=Image.new('RGBA',(w,h));maskpts=[];gx,gy=m['grip'];tx,ty=m['tip'];vx,vy=tx-gx,ty-gy;length=math.hypot(vx,vy)
  for y in range(h):
   for x in range(w):
    idx=raw[(h-1-y)*w+x];rgb=tuple(p[idx*3:idx*3+3][::-1])
    if marked.getpixel((m['crop_origin'][0]+x,m['crop_origin'][1]+y)) not in sentinels:continue
    assert rgb in wood
    wx=m['crop_origin'][0]+x-96;wy=m['crop_origin'][1]+y;along=((wx-gx)*vx+(wy-gy)*vy)/length
    color=wood[rgb]
    if -10<along<3:color=(40,48,56) # dark wrapped handle; existing black wrap pixels remain untouched
    if 10<=along<=11.5:color=(208,216,232) # restrained transition ring
    im.putpixel((x,y),(*colors[quant(color)],255));maskpts.append([x,y])
  assert maskpts
  part=export(im,h%2) if f else dict(resource=-1,x=0,y=0,width=w,height=h)
  part.update(origin=[m['crop_origin'][0]+part['x']-96,m['crop_origin'][1]+part['y']-92],source=m['name'],wood_pixels=len(maskpts),parent_height=h)
  im.save(O/f'{actor}-swing-{f}.png');im.getchannel('A').save(O/f'{actor}-swing-{f}-mask.png');poses.append(part)
 overlays.append(poses)
m=dict(parent='1eacf2bee026a058d179edf1c0b30888798f9316',palette='assets/gallery/GB0.TGA',source_sha256=hashlib.sha256((O/'source/aluminum-bat-guide.png').read_bytes()).hexdigest(),resources=res,texture_bytes=total,slots=len(res),carry=cp,hands=hands,overlays=overlays,boot_bytes=401952+total,free_bytes=56536-total)
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
h='#ifndef MF_RUNNING_BAT_VISUAL_DATA_H\n#define MF_RUNNING_BAT_VISUAL_DATA_H\n#define MF_RBV_NEW %d\n#define MF_RBV_BYTES %du\nstatic const mf_polish_resource rbv_resources[MF_RBV_NEW]={\n'%(len(res),total)
h+=',\n'.join('{"%s",%d,%d,%du}'%(r['name'],r['width'],r['height'],r['bytes']) for r in res)+'};\nstatic const short rbv_hands[2][4][2]='+json.dumps(hands).replace('[','{').replace(']','}')+';\n'
h+='static const short rbv_carry[3]={%d,%d,%d};\n'%(cp['resource'],cp['grip'][0],cp['grip'][1])
h+='static const short rbv_overlay[2][7][3]={'+','.join('{'+','.join('{%d,%d,%d}'%(p['resource'],p['origin'][0],p['origin'][1]) for p in a)+'}' for a in overlays)+'};\n#endif\n';(R/'src/running_bat_visual_data.h').write_text(h)
assert m['free_bytes']>0
print('Shared visual resources',len(res),'bytes',total,'total VDP1',m['boot_bytes'],'free',m['free_bytes'])
# Native/nearest previews are actual reusable texture composition, no concept legs.
for a,name in enumerate(['buck','chuck']):
 ims=[]
 for f in range(4):
  body=Image.open(R/f'assets/running/{name}-{f}.png').convert('RGBA');im=Image.new('RGBA',(128,96));hx,hy=hands[a][f];im.alpha_composite(carry,(hx-24,hy-32));im.alpha_composite(body);ims.append(im);im.save(O/f'{name}-run-{f}.png')
 for z in [1,4]:
  sheet=Image.new('RGBA',(512,96))
  for f,im in enumerate(ims):sheet.alpha_composite(im,(128*f,0))
  sheet.resize((512*z,96*z),Image.Resampling.NEAREST).save(O/f'{name}-contact-{z}x.png')
  gifs=[im.resize((128*z,96*z),Image.Resampling.NEAREST) for im in ims];gifs[0].save(O/f'{name}-run-{z}x.gif',save_all=True,append_images=gifs[1:],duration=100,loop=0,disposal=2)
# Review-only transitions assembled from the same native sprites, not concept art.
from PIL import ImageDraw
import shutil

def tga(path):
 b=path.read_bytes();w,h=struct.unpack_from('<HH',b,12);p=b[18:786];r=b[786:];im=Image.new('RGBA',(w,h));im.putdata([(*p[3*i:3*i+3][::-1],255) if i else (0,0,0,0) for y in range(h) for i in r[(h-1-y)*w:(h-y)*w]]);return im
for a,name in enumerate(['buck','chuck']):
 frames=[];labels=[];times=[]
 for f in range(4):
  im=Image.new('RGBA',(192,96));im.alpha_composite(Image.open(O/f'{name}-run-{f}.png'),(32,0));frames.append(im);labels.append('RUN '+str(f+1));times.append(100)
 frames.append(frames[-1].copy());labels.append('CARRY WINDUP');times.append(70)
 lowermeta=meta['legs'];lower=tga(R/'assets/cd'/lowermeta['name'])
 for f,duration in [(1,100),(2,30),(3,50),(4,50),(5,130),(6,150)]:
  im=Image.new('RGBA',(192,96));im.alpha_composite(lower,(96-lowermeta['anchor'][0],92-lowermeta['anchor'][1]));uppermeta=meta[name][f];im.alpha_composite(tga(R/'assets/cd'/uppermeta['name']),(96-uppermeta['anchor'][0],92-uppermeta['anchor'][1]));im.alpha_composite(Image.open(O/f'{name}-swing-{f}.png'),(96-uppermeta['anchor'][0],92-uppermeta['anchor'][1]));frames.append(im);labels.append(uppermeta['pose'].upper());times.append(duration)
 idle=Image.new('RGBA',(192,96));idle.alpha_composite(Image.open(R/f'assets/animation-polish/{name}-00.png'),(32,0));frames.append(idle);labels.append('RETURN IDLE');times.append(300)
 for z in [1,4]:
  gifs=[im.resize((192*z,96*z),Image.Resampling.NEAREST) for im in frames];gifs[0].save(O/f'{name}-transition-{z}x.gif',save_all=True,append_images=gifs[1:],duration=times,loop=0,disposal=2)
  sheet=Image.new('RGBA',(768,336),(16,20,32,255));draw=ImageDraw.Draw(sheet)
  for f,im in enumerate(frames):x=f%4*192;y=f//4*112;sheet.alpha_composite(im,(x,y));draw.text((x+3,y+97),labels[f],fill='white')
  sheet.resize((768*z,336*z),Image.Resampling.NEAREST).save(O/f'{name}-transition-sheet-{z}x.png')
 # The permitted bounded review retained the current leg artwork verbatim.
 legs=Image.new('RGBA',(512,112))
 for f in range(4):
  body=Image.open(R/f'assets/running/{name}-{f}.png');crop=body.crop((0,40,128,96));legs.alpha_composite(crop,(128*f,0));legs.alpha_composite(crop,(128*f,56))
 legs.save(O/f'{name}-leg-before-after-native.png');legs.resize((2048,448),Image.Resampling.NEAREST).save(O/f'{name}-leg-before-after-4x.png')
 shutil.copyfile(R/f'assets/stride-fix/{name}-identity-4x.png',O/f'{name}-leg-identity-4x.png')
