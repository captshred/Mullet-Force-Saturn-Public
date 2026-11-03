#!/usr/bin/env python3
"""Localized swagger leg import, fixed palette, exact shared-piece interning.
Explicit offline authoring command; normal builds never regenerate artwork.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,struct,re
R=Path(__file__).resolve().parents[1];O=R/'assets/swagger-walk';P=R/'assets/animation-polish';old=json.loads((P/'manifest.json').read_text())
for stale in O.glob('S[0-9][0-9][0-9].TGA'):stale.unlink()
palette=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786];colors=[tuple(palette[i*3:i*3+3][::-1]) for i in range(256)];memo={}
def quant(c):
 c=tuple(c)
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def indexed(im):return [[quant(im.getpixel((x,y))[:3]) if im.getpixel((x,y))[3]>=128 else 0 for x in range(128)] for y in range(96)]
def image(a):
 im=Image.new('RGBA',(128,96));im.putdata([(*colors[v],255) if v else (0,0,0,0) for row in a for v in row]);return im
src=Image.open(O/'source/leg-edit-guide.png').convert('RGBA');w,h=src.size
alpha=src.getchannel('A');rows=[sum(v>=128 for v in alpha.crop((0,y,w,y+1)).getdata()) for y in range(h)]
mid=min(range(h//2-60,h//2+61),key=lambda y:(rows[y],abs(y-h//2)))
pose_sources=[5,4,8];natives=[]
for actor,name in enumerate(['buck','chuck']):
 band=src.crop((0,0 if actor==0 else mid,w,mid if actor==0 else h));al=band.getchannel('A');projection=[sum(v>=128 for v in al.crop((x,0,x+1,band.height)).getdata()) for x in range(w)]
 cuts=[0]+[min(range(round(i*w/3)-60,round(i*w/3)+61),key=lambda x:(projection[x],abs(x-i*w/3))) for i in [1,2]]+[w]
 frames=[]
 for phase,f in enumerate(pose_sources):
  im=band.crop((cuts[phase],0,cuts[phase+1],band.height));box=im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();crop=im.crop(box);nw=round(crop.width*88/crop.height)
  crop=crop.convert('RGBa').resize((nw,88),Image.Resampling.LANCZOS).convert('RGBA');native=Image.new('RGBA',(128,96));native.alpha_composite(crop,(64-nw//2,4))
  original=Image.open(P/f'{name}-{f:02d}.png').convert('RGBA');oa=original.getchannel('A');ga=native.getchannel('A')
  dx=min(range(-8,9),key=lambda d:(sum(bool(oa.getpixel((x,y)))!=bool(ga.getpixel((x-d,y))) for y in range(8,49) for x in range(24,105) if 0<=x-d<128),abs(d)))
  registered=Image.new('RGBA',(128,96));registered.alpha_composite(native,(dx,0));original.paste(registered.crop((0,52,128,96)),(0,52));a=indexed(original);im=image(a)
  assert im.getbbox()[1:4:2]==(4,92)
  assert im.crop((0,0,128,52)).tobytes()==Image.open(P/f'{name}-{f:02d}.png').convert('RGBA').crop((0,0,128,52)).tobytes()
  im.save(O/f'{name}-{phase:02d}.png');frames.append(a)
 natives.append(frames)
resources=list(old['resources']);pool={}
for rid,p in enumerate(resources):
 if rid<42:
  actor,frame,part=p['old_ref'];path=R/('assets/gallery' if frame==0 else 'assets/animation-study')/p['name']
 else:path=P/p['name']
 pool[p['width'],p['height'],path.read_bytes()[786:]]=rid
oldcount=len(resources);newfiles={};actors=[];required=set();naive=0
for actor in old['actors']:
 for f in actor['frames'][:4]:required.update(p['resource'] for p in f['parts'])
for ai,name in enumerate(['buck','chuck']):
 frames=[]
 for f,a in enumerate(natives[ai]):
  im=image(a);parts=[]
  def cost(cut):
   total=0
   for t,b in [(48,cut),(cut,96)]:
    x,y,x2,y2=im.crop((0,t,128,b)).getbbox();ww=((x2-x+7)//8)*8;hh=y2-y
    if hh%2:return 10**8
    total+=(ww*hh+31)&~31
   return total
  cut=min(range(68,89,2),key=lambda c:(cost(c),abs(c-80)))
  for top,bottom in [(0,48),(48,cut),(cut,96)]:
   x,y,x2,y2=im.crop((0,top,128,bottom)).getbbox();y+=top;y2+=top;ww=((x2-x+7)//8)*8;hh=y2-y
   payload=bytes(a[yy][xx] if xx<x2 else 0 for yy in range(y2-1,y-1,-1) for xx in range(x,x+ww));key=(ww,hh,payload);size=(ww*hh+31)&~31;naive+=size
   if key not in pool:
    fn=f'S{len(newfiles):03d}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,ww,hh);head[16]=8
    data=bytes(head)+palette+payload;(O/fn).write_bytes(data);newfiles[fn]=hashlib.sha256(data).hexdigest();pool[key]=len(resources);resources.append({'name':fn,'source':'swagger','width':ww,'height':hh,'aligned_bytes':size})
   rid=pool[key];required.add(rid);parts.append({'resource':rid,'x':x,'y':y,'width':ww,'height':hh})
  frames.append({'frame':f,'parts':parts,'upper_source_frame':pose_sources[f],'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'floor_x':[x for x in range(128) if a[91][x]],'bounds':list(im.getbbox())})
 actors.append({'name':name,'frames':frames})
newbytes=sum(p['aligned_bytes'] for p in resources[oldcount:]);galleryids={0,1,2,21,22,23};boot=302336+sum(resources[r]['aligned_bytes'] for r in required-galleryids);full=427104+newbytes
assert full<=458488 and len(resources)+95-6<255
m={'baseline':'05b53c0e6d70032b1cf37582a86f64deb0fa7ce2','canvas':[128,96],'root':[64,92],'standing_height':88,'palette_sha256':hashlib.sha256(palette).hexdigest(),'guide_sha256':hashlib.sha256((O/'source/leg-edit-guide.png').read_bytes()).hexdigest(),'old_resource_count':oldcount,'resources':resources,'new_texture_bytes':newbytes,'naive_piece_bytes':naive,'boot_vdp1_bytes':boot,'boot_free_bytes':458488-boot,'expanded_vdp1_bytes':full,'expanded_free_bytes':458488-full,'boot_required':sorted(required),'boot_sprite_count':95+len(required-galleryids)+6,'expanded_sprite_count':95+len(resources),'actors':actors,'tga_sha256':newfiles}
(O/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
res='\n'.join('{"%s",%d,%d,%d},'%(p['name'],p['width'],p['height'],p['aligned_bytes']) for p in resources[oldcount:]);parts=',\n'.join('{'+','.join('{'+','.join('{%d,%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width'],p['height']) for p in f['parts'])+'}' for f in a['frames'])+'}' for a in actors)
(R/'src/swagger_data.h').write_text('/* Generated three-pose native swagger resources, existing pool IDs retained. */\n#ifndef MF_SWAGGER_DATA_H\n#define MF_SWAGGER_DATA_H\n#define MF_SWAGGER_NEW %d\n#define MF_SWAGGER_BOOT_BYTES %du\n#define MF_SWAGGER_FULL_BYTES %du\nstatic const mf_polish_resource swagger_resources[MF_SWAGGER_NEW]={\n%s\n};\nstatic const unsigned char swagger_required[%d]={%s};\nstatic const mf_polish_piece swagger_parts[2][3][3]={\n%s\n};\n#endif\n'%(len(newfiles),boot,full,res,len(resources),','.join(str(int(i in required)) for i in range(len(resources))),parts))
# Review sheet and palette-exact animated files.
sheet=Image.new('RGB',(384,232),(27,31,43));d=ImageDraw.Draw(sheet)
timing=(R/'src/swagger_timing.h').read_text();holds=[list(map(int,re.search(n+r'_HOLDS\s+\{([^}]+)',timing).group(1).split(','))) for n in ['MF_SWAGGER_BUCK','MF_SWAGGER_CHUCK']]
for ai,name in enumerate(['buck','chuck']):
 for f,a in enumerate(natives[ai]):
  im=image(a);sheet.paste(im,(128*f,116*ai),im);d.line((128*f,116*ai+92,128*f+127,116*ai+92),fill=(88,112,110));d.text((128*f+2,116*ai+98),f'{name} swagger {f+1}',fill=(240,240,245))
 ims=[]
 for a in natives[ai]:
  g=Image.new('P',(128,96));g.putpalette([v for c in colors for v in c]);g.putdata([v for row in a for v in row]);ims.append(g.resize((384,288),Image.Resampling.NEAREST))
 ims[0].save(O/f'{name}-swagger.gif',save_all=True,append_images=ims[1:],duration=[round(t*100/60)*10 for t in holds[ai]],loop=0,transparency=0,disposal=2,optimize=False)
sheet.save(O/'swagger-contact-native.png');sheet.resize((1152,696),Image.Resampling.NEAREST).save(O/'swagger-contact-3x.png')
print(json.dumps({k:m[k] for k in ['new_texture_bytes','boot_vdp1_bytes','boot_free_bytes','expanded_vdp1_bytes','expanded_free_bytes','boot_sprite_count','expanded_sprite_count']},indent=2))
