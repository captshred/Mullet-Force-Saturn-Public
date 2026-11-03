#!/usr/bin/env python3
"""Localized edited-guide import: lock all but leading leg, preserve TGA layouts."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,struct,shutil
R=Path(__file__).resolve().parents[1];O=R/'assets/knee-lift';B=R/'assets/original-three-walk';meta=json.loads((B/'manifest.json').read_text());palette=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(palette[i*3:i*3+3][::-1]) for i in range(256)];memo={}
def quant(c):
 c=tuple(c)
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
src=Image.open(O/'source/frame1-edit.png').convert('RGBA');src.putdata([p if p[3]>=240 else (0,0,0,0) for p in src.getdata()]);w,h=src.size
alpha=src.getchannel('A');projection=[sum(bool(v) for v in alpha.crop((x,0,x+1,h)).getdata()) for x in range(w)];cut=min(range(w//2-100,w//2+101),key=lambda x:(projection[x],abs(x-w//2)));cuts=[0,cut,w];actors=[];tgas={}
for a,n in enumerate(['buck','chuck']):
 old=Image.open(B/f'{n}-00.png').convert('RGBA');shutil.copy(B/f'{n}-00.png',O/'before'/f'{n}-00.png')
 cell=src.crop((cuts[a],0,cuts[a+1],h));crop=cell.crop(cell.getchannel('A').getbbox());nw=round(crop.width*88/crop.height);crop=crop.convert('RGBa').resize((nw,88),Image.Resampling.LANCZOS).convert('RGBA');candidate=Image.new('RGBA',(128,96));candidate.alpha_composite(crop,(64-nw//2,4));oa=old.getchannel('A');ga=candidate.getchannel('A')
 dx=min(range(-10,11),key=lambda d:(sum(bool(oa.getpixel((x,y)))!=bool(ga.getpixel((x-d,y))) for y in range(8,52) for x in range(24,105) if 0<=x-d<128),abs(d)))
 guide=Image.new('RGBA',(128,96));guide.alpha_composite(candidate,(dx,0));im=old.copy()
 for y in range(56,92):
  for x in range(72 if y<58 else 64,100 if y<80 else 102):
   p=guide.getpixel((x,y));im.putpixel((x,y),(*colors[quant(p[:3])],255) if p[3]>=128 else (0,0,0,0))
 im.save(O/f'{n}-00.png')
 for f in [1,2]:shutil.copy(B/f'{n}-{f:02d}.png',O/f'{n}-{f:02d}.png')
 changed=[(x,y) for y in range(96) for x in range(128) if old.getpixel((x,y))!=im.getpixel((x,y))];front=[y for y in range(58,96) for x in range(64,102) if im.getpixel((x,y))[3]]
 for p in meta['actors'][a]['frames'][0]['parts'][1:]:
  blob=(R/'assets/animation-study'/p['name']).read_bytes();ww,hh=p['width'],p['height'];x0,y0=p['x'],p['y'];payload=[]
  for yy in range(y0+hh-1,y0-1,-1):
   for xx in range(x0,x0+ww):
    c=im.getpixel((xx,yy));offset=(y0+hh-1-yy)*ww+xx-x0
    payload.append(blob[786+offset] if old.getpixel((xx,yy))==c else quant(c[:3]) if c[3] else 0)
  data=blob[:786]+bytes(payload);assert len(data)==len(blob);(O/'overrides'/p['name']).write_bytes(data);tgas[p['name']]=hashlib.sha256(data).hexdigest()
 actors.append({'name':n,'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'changed_pixels':len(changed),'changed_bounds':[min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)+1,max(y for x,y in changed)+1],'front_sole_y':max(front),'rear_sole_y':max(y for y in range(96) for x in range(64) if im.getpixel((x,y))[3]),'guide_dx':dx})
# Pixel-exact before/after contact and 10-tick full cycle GIFs.
sheet=Image.new('RGB',(256,232),(27,31,43));draw=ImageDraw.Draw(sheet)
for a,n in enumerate(['buck','chuck']):
 for v,folder in enumerate([O/'before',O]):
  im=Image.open(folder/f'{n}-00.png').convert('RGBA');sheet.paste(im,(128*v,116*a),im);draw.line((128*v,116*a+92,128*v+127,116*a+92),fill=(88,112,110));draw.text((128*v+2,116*a+98),f'{n} {"after" if v else "before"}',fill=(240,240,245))
 ims=[]
 for f in range(3):
  im=Image.open(O/f'{n}-{f:02d}.png').convert('RGBA');g=Image.new('P',(128,96));g.putpalette([v for c in colors for v in c]);g.putdata([quant(c[:3]) if c[3] else 0 for c in im.getdata()]);ims.append(g.resize((384,288),Image.Resampling.NEAREST))
 ims[0].save(O/f'{n}-cycle.gif',save_all=True,append_images=ims[1:],duration=[170,160,170],loop=0,transparency=0,disposal=2,optimize=False)
sheet.save(O/'before-after-native.png');sheet.resize((1536,1392),Image.Resampling.NEAREST).save(O/'before-after-6x.png')
m={'baseline':'a44464fb557882cfb07afaeaf409ed6871cfcaf5','timing_ticks':[10,10,10],'canvas':[128,96],'root':[64,92],'palette_sha256':hashlib.sha256(palette).hexdigest(),'guide_sha256':hashlib.sha256((O/'source/frame1-edit.png').read_bytes()).hexdigest(),'actors':actors,'overrides':tgas,'boot_bytes':351104,'free_bytes':107384,'full_bytes':427104,'frame2_3_sha256':{f'{n}-{f:02d}.png':hashlib.sha256((B/f'{n}-{f:02d}.png').read_bytes()).hexdigest() for n in ['buck','chuck'] for f in [1,2]}}
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(actors,indent=2))
