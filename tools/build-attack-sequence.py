#!/usr/bin/env python3
"""Targeted arm poses + exact prior jab/impact/carry source pieces. No game edits."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,struct,math
R=Path(__file__).resolve().parents[1];O=R/'assets/attack-sequence';pal=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(pal[3*i:3*i+3][::-1]) for i in range(256)];memo={};pool={};resources=[]
for p in list(O.glob('CA*.TGA'))+list(O.glob('*-key-*.png')):p.unlink()
def quant(c):
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def indexed(im):
 out=Image.new('RGBA',im.size);out.putdata([(*colors[quant(c[:3])],255) if c[3]>=160 else (0,0,0,0) for c in im.getdata()]);return out

def pieces(im):
 out=[]
 for y in range(0,112,16):
  strip=im.crop((0,y,160,min(112,y+16)));box=strip.getbbox()
  if not box:continue
  l,t,r,b=box;w=math.ceil((r-l)/8)*8;h=b-t;h+=h%2
  a=bytes(quant(strip.getpixel((x,yy))[:3]) if strip.getpixel((x,yy))[3] else 0 for yy in range(t,t+h) for x in range(l,l+w)) if l+w<=160 and t+h<=16 else bytes(quant(strip.getpixel((x,yy))[:3]) if x<160 and yy<16 and strip.getpixel((x,yy))[3] else 0 for yy in range(t,t+h) for x in range(l,l+w))
  key=(w,h,a)
  if key not in pool:
   rid=len(resources);pool[key]=rid;name=f'CA{rid:02}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,w,h);head[16]=8;blob=bytes(head)+pal+b''.join(a[q*w:(q+1)*w] for q in range(h-1,-1,-1));(O/name).write_bytes(blob);resources.append(dict(name=name,width=w,height=h,bytes=(w*h+31)&~31,sha256=hashlib.sha256(blob).hexdigest()))
  out.append(dict(resource=pool[key],x=l,y=y+t,width=w,height=h))
 return out
source=Image.open(O/'source/arm-arc-guide.png').convert('RGBA');allparts=[];lowers=[];metas=[]
for actor,name in enumerate(['buck','chuck']):
 idle=Image.open(R/f'assets/animation-polish/{name}-00.png').convert('RGBA');planted=Image.open(R/f'assets/bat-momentum/{name}-key-3.png').crop((0,64,160,112));low=Image.new('RGBA',(160,112));low.alpha_composite(planted,(0,64));lowers.append(pieces(low));keys=[]
 for original in [1,3]:
  im=Image.new('RGBA',(160,112));im.alpha_composite(Image.open(R/f'assets/bat-momentum/{name}-key-{original}.png').crop((0,0,160,64)));keys.append(im)
 # Three arm-only edits from source guide. Same body scale in all cells.
 for f,cx in [(1,760),(0,270)]:
  sy=85 if actor==0 else 575;foot=490 if actor==0 else 982;scale=88/(foot-sy)
  # Explicit belt registrations, not shared sheet-cell origins.
  cx+=([0,0,0] if actor==0 else [3,6,3])[f]
  im=source.transform((160,112),Image.Transform.AFFINE,(1/scale,0,cx-64/scale,0,1/scale,sy-20/scale),Image.Resampling.NEAREST);im=indexed(im)
  # Keep only torso/arms above waist and arm/weapon region below it.
  mask=Image.new('L',(160,112),0);d=ImageDraw.Draw(mask);d.rectangle((0,0,159,63),fill=255)
  if f==1:d.polygon([(77,57),(90,58),(121,78),(118,84),(79,68)],fill=255)
  if f==2:d.polygon([(62,57),(80,59),(86,75),(110,99),(105,105),(75,78),(66,72)],fill=255)
  for y in range(112):
   for x in range(160):
    sx=cx+(x-64)/scale;sypos=sy+(y-20)/scale
    if not mask.getpixel((x,y)) or sx<f*512 or sx>=(f+1)*512 or sypos<actor*512 or sypos>=(actor+1)*512:im.putpixel((x,y),(0,0,0,0))
  # Preserve original facial/hair pixels; the forward bridge uses a small native
  # lean (8 right/2 down), never a new face or a scaled head.
  saved=im.copy();hx,hy=(0,0);im.paste((0,0,0,0),(39,16,97,40))
  if f==0:
   for yy in range(16,40):
    for xx in range(78,105):
     c=saved.getpixel((xx,yy))
     if c[3] and max(c[:3])-min(c[:3])<60 and max(c[:3])>=80:im.putpixel((xx,yy),c)
  head=idle.crop((39,0,89,24));im.alpha_composite(head,(39+hx,16+hy))
  if f==0:
   # Normalize only the new silver barrel length to the approved carried bat.
   # Hands, arm pixels and original face remain fixed; no body/pose scaling.
   gx,gy=77,44;vx,vy=23,-33;length=math.hypot(vx,vy);ux,uy=vx/length,vy/length;metal=Image.new('RGBA',(160,112))
   for yy in range(3,43):
    for xx in range(78,112):
     c=im.getpixel((xx,yy));along=(xx-gx)*ux+(yy-gy)*uy;across=abs((xx-gx)*uy-(yy-gy)*ux)
     if c[3] and along>8 and across<=5 and max(c[:3])-min(c[:3])<70 and max(c[:3])>=80:metal.putpixel((xx,yy),c);im.putpixel((xx,yy),(0,0,0,0))
   for yy in range(3,43):
    for xx in range(78,112):
     along=(xx-gx)*ux+(yy-gy)*uy;perp=-(xx-gx)*uy+(yy-gy)*ux;sx=round(gx+along/.9*ux-perp*uy);syy=round(gy+along/.9*uy+perp*ux)
     if 0<=sx<160 and 0<=syy<112 and metal.getpixel((sx,syy))[3]:im.putpixel((xx,yy),metal.getpixel((sx,syy)))
  im.alpha_composite(head,(39+hx,16+hy))
  keys.append(im)
 # Four cropped real running uppers; weapon remains the one existing RBV texture.
 for f in range(4):
  im=Image.new('RGBA',(160,112));im.alpha_composite(Image.open(R/f'assets/running/{name}-{f}.png').crop((0,0,128,48)),(0,16));keys.append(im)
 parts=[]
 for f,upper in enumerate(keys):
  parts.append(pieces(upper));full=low.copy()
  if f>=4:
   hx,hy=json.loads((R/'assets/running-bat-visual/manifest.json').read_text())['hands'][actor][f-4];full.alpha_composite(Image.open(R/'assets/running-bat-visual/carry-native.png'),(hx-24,16+hy-32))
  full.alpha_composite(upper);full.save(O/f'{name}-key-{f}.png')
 allparts.append(parts)
 # Contact sheet includes only the defined attack keys and actual carry entries.
 sheet=Image.new('RGBA',(800,256),(16,20,32,255));draw=ImageDraw.Draw(sheet)
 for f in range(8):
  full=Image.open(O/f'{name}-key-{f}.png');sheet.alpha_composite(full,(f%5*160,f//5*128));draw.text((f%5*160+2,f//5*128+113),['JAB','IMPACT','FORWARD DOWN','FOLLOW UP','CARRY 1','CARRY 2','CARRY 3','CARRY 4'][f],fill='white')
 sheet.save(O/f'{name}-contact-native.png');sheet.resize((3200,1024),Image.Resampling.NEAREST).save(O/f'{name}-contact-4x.png')
# Two palette-identical, shared rear-sweep rotations of the approved carry bat.
weapon_source=Image.open(R/'assets/running-bat-visual/carry-native.png').convert('RGBA');weapons=[]
for angle in [-180,-225]:
 delta=math.radians(angle-math.degrees(math.atan2(-30,-20)));co,si=math.cos(delta),math.sin(delta)
 weapon=weapon_source.transform((80,80),Image.Transform.AFFINE,(co,si,24-40*co-40*si,-si,co,32+40*si-40*co),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(160,112));canvas.alpha_composite(weapon);weapons.append(pieces(canvas));weapon.save(O/f'rear-bat-{angle}.png')
total=sum(r['bytes'] for r in resources);m=dict(parent='1686681ee6ff4bedd100d94bad914c7dca8dcd81',canvas=[160,112],root=[64,108],palette='assets/gallery/GB0.TGA',resources=resources,frames=allparts,lowers=lowers,weapons=weapons,texture_bytes=total,boot_bytes=410464+total,free_bytes=48024-total,slots=169+len(resources),key_names=['jab','impact','forward_down','follow_up','carry0','carry1','carry2','carry3']);(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(total,m['boot_bytes'],m['free_bytes'],m['slots']);assert m['free_bytes']>=0

def arr(v):return '{'+','.join('{%d,%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width'],p['height']) for p in v)+',{-1,0,0,0,0}}'
h='#ifndef MF_ATTACK_SEQUENCE_DATA_H\n#define MF_ATTACK_SEQUENCE_DATA_H\n#define MF_CA_NEW %d\n#define MF_CA_BYTES %du\n'%(len(resources),total)
h+='static const mf_polish_resource ca_resources[MF_CA_NEW]={'+','.join('{"%s",%d,%d,%du}'%(r['name'],r['width'],r['height'],r['bytes']) for r in resources)+'};\n'
h+='static const mf_polish_piece seq_upper[2][8][%d]={'%(max(len(v) for actor in allparts for v in actor)+1)+','.join('{'+','.join(arr(v) for v in actor)+'}' for actor in allparts)+'};\n'
h+='static const mf_polish_piece seq_weapon[2][%d]={'%(max(map(len,weapons))+1)+','.join(arr(v) for v in weapons)+'};\n'
h+='static const mf_polish_piece seq_lower[2][%d]={'%(max(map(len,lowers))+1)+','.join(arr(v) for v in lowers)+'};\n#endif\n';(R/'src/attack_sequence_data.h').write_text(h)
