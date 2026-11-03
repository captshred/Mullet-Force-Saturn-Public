#!/usr/bin/env python3
"""Deterministic native-pixel polish plus reviewed opposite-stride leg edits.
Art direction: fixed identity/pelvis; hand-registered support points, small cluster
translations, shallow far-leg shade, localized edited-guide sole highlights.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,struct,shutil
R=Path(__file__).resolve().parents[1];O=R/'assets/animation-polish';O.mkdir(exist_ok=True)
for stale in O.glob('P[0-9][0-9][0-9].TGA'):stale.unlink()
P=R/'assets/animation-study';old=json.loads((P/'manifest.json').read_text())
palette=(R/'assets/gallery/GB0.TGA').read_bytes()[18:786]
colors=[tuple(palette[i*3:i*3+3][::-1]) for i in range(256)];memo={}
def quant(c):
 c=tuple(c)
 if c not in memo:memo[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return memo[c]
def read(path):
 im=Image.open(path).convert('RGBA');return [[quant(im.getpixel((x,y))[:3]) if im.getpixel((x,y))[3]>=128 else 0 for x in range(128)] for y in range(96)]
def image(a):
 im=Image.new('RGBA',(128,96));im.putdata([(*colors[i],255) if i else (0,0,0,0) for row in a for i in row]);return im

def shift_cluster(a,points,dx,dy):
 # Rigid integer-pixel translations; no interpolation/resizing of native pixels.
 b=[row[:] for row in a]
 for x,y in points:
  # Restore interior from an adjacent original cluster pixel instead of making
  # a transparent tear in clothing. Silhouette pixels clear to transparency.
  interior=all(0<=x+u<128 and 0<=y+v<96 and a[y+v][x+u] for u,v in [(-1,0),(1,0),(0,-1),(0,1)])
  b[y][x]=a[min(95,y-dy)][max(0,min(127,x-dx))] if interior else 0
 for x,y in points:
  if 0<=x+dx<128 and 0<=y+dy<96:b[y+dy][x+dx]=a[y][x]
 return b

def hair(a,name,dx,dy):
 pts=[]
 for y in range(24,34):
  for x in range(30 if name=='chuck' else 41,62):
   i=a[y][x]
   if not i:continue
   r,g,b=colors[i]
   match=(r>g*1.35 and g<90 and b<70) if name=='chuck' else (r>130 and g>80 and r>g*1.05 and b<120)
   if match:pts.append((x,y))
 return shift_cluster(a,pts,dx,dy) if pts and (dx or dy) else a

def cloth(a,name,amount):
 if not amount:return a
 # Only small shoulder/lapel/chest regions. Face, gloves, belt and feet stay.
 pts=[]
 for y in range(28,44):
  for x in range(43,82):
   i=a[y][x]
   if not i:continue
   r,g,b=colors[i]
   garment=(max(r,g,b)-min(r,g,b)<65 and b>=r-15) if name=='buck' else (b>r+8 and b>g)
   if garment and ((x<55 and y<34) or (57<=x<=71 and 34<=y<=42)):pts.append((x,y))
 return shift_cluster(a,pts,0,-1)

def guide_frames():
 src=Image.open(O/'boot-edit-guide.png').convert('RGBA');w,h=src.size;result=[]
 for actor in range(2):
  band=src.crop((0,actor*h//2,w,(actor+1)*h//2));alpha=band.getchannel('A')
  proj=[sum(v>=128 for v in alpha.crop((x,0,x+1,band.height)).getdata()) for x in range(w)];cuts=[0]
  for i in range(1,6):
   t=round(i*w/6);cut=min(range(t-45,t+46),key=lambda x:(proj[x],abs(x-t)));assert not proj[cut];cuts.append(cut)
  cuts.append(w);frames=[]
  for f in range(6):
   cell=band.crop((cuts[f],0,cuts[f+1],band.height));bbox=cell.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();crop=cell.crop(bbox)
   nw=round(crop.width*88/crop.height);crop=crop.convert('RGBa').resize((nw,88),Image.Resampling.LANCZOS).convert('RGBA')
   im=Image.new('RGBA',(128,96));im.alpha_composite(crop,(64-nw//2,4))
   frames.append([[quant(im.getpixel((x,y))[:3]) if im.getpixel((x,y))[3]>=128 else 0 for x in range(128)] for y in range(96)])
  result.append(frames)
 return result
G=guide_frames()
# No duplicate bytes among original pieces. Seed the interning table so a
# translated/polished piece reuses an existing ID whenever its pixels match.
pool={};resources=[];oldrefs=[]
for a,actor in enumerate(old['actors']):
 for frame in actor['frames']:
  for part,p in enumerate(frame['parts']):
   path=R/'assets/gallery'/p['name'] if not frame['frame'] else P/p['name'];blob=path.read_bytes()
   key=(p['width'],p['height'],blob[786:]);rid=len(resources)
   resources.append({'name':p['name'],'source':'original','old_ref':[a,frame['frame'],part],'width':p['width'],'height':p['height'],'aligned_bytes':p['aligned_bytes']})
   assert key not in pool;pool[key]=rid
newfiles={};newbytes=0;naivebytes=0;actors=[];allparts=[];guide_changes=0
for ai,name in enumerate(['buck','chuck']):
 original=[read(P/f'{name}-{f:02d}.png') for f in range(7)];base=original[0];canon=original[1]
 idles=[base]
 for phase in range(1,4):
  amt=([0,1,1,0] if name=='buck' else [0,0,1,1])[phase]
  a=cloth([row[:] for row in base],name,amt)
  a=hair(a,name,([0,1,1,1] if name=='buck' else [0,1,1,0])[phase],([0,0,1,0] if name=='buck' else [0,0,1,1])[phase])
  idles.append(a)
 assert len({image(a).tobytes() for a in idles})==4,'Breathing needs four distinct native phases'
 walks=[];landmarks=[]
 pelvis=[66,64,66,65,63,66] if name=='buck' else [66,64,67,65,64,67]
 for phase in range(6):
  src=original[phase+1];dx=66-pelvis[phase]
  # Register the old lower pixels under the canonical pelvis without scaling.
  a=[row[:] for row in canon]
  for y in range(49,96):a[y]=[src[y][x-dx] if 0<=x-dx<128 else 0 for x in range(128)]
  target=[80,72,64,80,72,64][phase]
  heel=min(x for x in range(60,128) if a[91][x]);delta=target-heel
  # Small lateral leg rotation: rows translate by integer pixels, retaining
  # each row's pixel widths; upper thigh fixed, ankle at the registered target.
  b=[row[:] for row in a]
  for y in range(60,96):
   d=round(delta*min(1,(y-60)/24));cut=60 if phase%3==2 else 64
   for x in range(cut,128):b[y][x]=0
   for x in range(cut,128):
    if a[y][x] and 0<=x+d<128:b[y][x+d]=a[y][x]
  a=b
  # Legacy three-pose prototype shading. This alone did not alternate
  # the gait; corrected second-half leg geometry is imported below.
  for y in range(51,89):
   cut=60 if phase%3==2 else 64
   for x in range(128):
    far=(x<cut) if phase<3 else (x>=cut)
    i=a[y][x]
    if far and i:
     r,g,b=colors[i]
     if max(r,g,b)<185:a[y][x]=quant((round(r*.94),round(g*.94),round(b*.96)))
  # Lift the trailing boot/cuff in the down pose; keep the support sole fixed.
  if phase%3==1:
   lift=2 if name=='buck' else 1;pts=[(x,y) for y in range(64,92) for x in range(0,60) if a[y][x]]
   a=shift_cluster(a,pts,0,-lift)
  floor=[x for x in range(60,128) if a[91][x]];assert min(floor)==target,(name,phase,floor,target)
  if phase%3==0:
   # Lead heel landing / rear toe-off: only one native pixel of sole roll.
   for x in floor:
    if x>target+4:a[90][x]=a[91][x];a[91][x]=0
   back=[x for x in range(60) if a[91][x]]
   if back:
    toe=max(back)
    for x in back:
     if x<toe-2:a[90][x]=a[91][x];a[91][x]=0
  # Import only conservative neutral sole-edge shade patches from the edited
  # guide, never a regenerated head, torso, leg silhouette or whole frame.
  for y in [89,90]:
   for x in range(target,target+5):
    i=a[y][x];j=G[ai][phase][y][max(0,min(127,x-dx-delta))]
    if i and j:
     c,d=colors[i],colors[j]
     if max(c)-min(c)<35 and max(d)-min(d)<35 and max(abs(c[k]-d[k]) for k in range(3))<=32 and i!=j:a[y][x]=j;guide_changes+=int(phase<3)
  a=cloth(a,name,phase in ([1,4] if name=='buck' else [2,5]))
  a=hair(a,name,[0,1,0,0,1,0][phase],0 if name=='buck' else [0,0,1,1,0,0][phase])
  if phase>=3:
   corrected=read(O/'opposite-source'/f'{name}-{phase+1}.png')
   # Lock every approved upper-body pixel; edited source supplies legs only.
   for y in range(52,96):a[y]=corrected[y][:]
  walks.append(a)
  landmarks.append({'support_leg':'near' if phase<3 else 'far','heel_x':target,'floor_y':91,'legacy_root_advance':(phase%3)*5*390/256,'heel_world_keyframe':target+(phase%3)*5*390/256,'pelvis_registration_x':66,'pelvis_source_x':pelvis[phase],'lower_dx':dx,'support_ankle_dx':delta,'contact':'heel+rear toe' if phase%3==0 else 'full sole','trailing_lift_px':(2 if name=='buck' else 1) if phase%3==1 else 0})
 for phase in range(6):
  landmarks[phase]={'phase':['near contact','near down / far trails','near support / far passing','far contact / near trails','far down / near trails','far support / near passing'][phase],
   'floor_y':91,'pelvis_registration_x':66,'floor_x':[x for x in range(128) if walks[phase][91][x]],
   'geometry_source':'ebc9d79 exact' if phase<3 else 'opposite-source leg edit below row 52'}
 # One lowered-guard bridge, then the first breath pose. Existing pixels only.
 bridge=[row[:] for row in walks[0]]
 points=[(x,y) for y in range(24,46) for x in range(77,102) if bridge[y][x]]
 # The idle supplies the exposed costume beneath the lowering guard.
 original_bridge=[row[:] for row in bridge]
 for x,y in points:bridge[y][x]=base[y][x]
 for x,y in points:
  if y+3<96:bridge[y+3][x]=original_bridge[y][x]
 for yy in range(4,32):
  for xx in range(64,80):bridge[yy][xx]=canon[yy][xx]
 poses=idles+walks+[bridge,idles[1]]
 outframes=[];actorparts=[]
 for f,a in enumerate(poses):
  im=image(a);im.save(O/f'{name}-{f:02d}.png');bbox=im.getbbox();assert bbox[1]==4 and bbox[3]==92
  parts=[]
  # Share the unchanged upper walking artwork as one larger piece.
  # Head/face pixels do not change; this saves more than six separate torsos.
  headcut=48 if 4<=f<=9 else 24
  split=80
  if 7<=f<=9:
   # Same three pieces; choose an even split that minimizes padded texture
   # storage without modifying a single source pixel or changing anchors.
   def split_cost(cut):
    total=0
    for t,b in [(headcut,cut),(cut,96)]:
     box=im.crop((0,t,128,b)).getbbox()
     if box is None:return 10**9
     x,y,x2,y2=box;pw=((x2-x+7)//8)*8;ph=y2-y
     if ph%2:return 10**9 # retain the validated SGL raster registration
     total+=(pw*ph+31)&~31
    return total
   split=min(range(68,89,2),key=lambda cut:(split_cost(cut),abs(cut-80)))
  for part,(top,bottom) in enumerate([(0,headcut),(headcut,split),(split,96)]):
   box=im.crop((0,top,128,bottom)).getbbox();assert box;x,y,x2,y2=box;y+=top;y2+=top;pw=((x2-x+7)//8)*8;ph=y2-y
   payload=bytes(a[yy][xx] if xx<x2 else 0 for yy in range(y2-1,y-1,-1) for xx in range(x,x+pw));size=(pw*ph+31)&~31;naivebytes+=size
   key=(pw,ph,payload)
   if key not in pool:
    n=len(newfiles);fn=f'P{n:03d}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,pw,ph);head[16]=8
    blob=bytes(head)+palette+payload;(O/fn).write_bytes(blob);newfiles[fn]=hashlib.sha256(blob).hexdigest();newbytes+=size
    pool[key]=len(resources);resources.append({'name':fn,'source':'polish','width':pw,'height':ph,'aligned_bytes':size})
   rid=pool[key];parts.append({'resource':rid,'name':resources[rid]['name'],'x':x,'y':y,'width':pw,'height':ph})
  outframes.append({'frame':f,'kind':'idle' if f<4 else 'walk' if f<10 else 'bridge','parts':parts,'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'bounds':list(bbox)})
  actorparts.append('{'+','.join('{%d,%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width'],p['height']) for p in parts)+'}')
 actors.append({'name':name,'idle_ticks':[24,16,24,16] if name=='buck' else [30,18,24,18],'frames':outframes,'walk_landmarks':landmarks})
 allparts.append('{'+','.join(actorparts)+'}')
 # Exact indexed GIF output, no adaptive re-quantization or new palette.
 for mode,indices,durations in [('idle',list(range(4)),[v*1000//60 for v in actors[-1]['idle_ticks']]),('walk',list(range(4,10)),[80,80,90,80,80,90])]:
  ims=[]
  for f in indices:
   g=Image.new('P',(128,96));g.putpalette([v for c in colors for v in c]);g.putdata([i for row in poses[f] for i in row]);g.info['transparency']=0;ims.append(g.resize((384,288),Image.Resampling.NEAREST))
  ims[0].save(O/f'{name}-{mode}.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,transparency=0,disposal=2,optimize=False)
(O/'prototype').mkdir(exist_ok=True)
for n in ['buck','chuck']:
 for f in range(7):shutil.copy(P/f'{n}-{f:02d}.png',O/'prototype'/f'{n}-{f:02d}.png')
manifest={'gait_checkpoint':'ebc9d79169bd91bbd982fb4c036041734618664f','checkpoint':'ff24c5ec160318c4eb07da171b684a00a1d973c8','canvas':[128,96],'root':[64,92],'standing_height':88,'palette_sha256':hashlib.sha256(palette).hexdigest(),'walk_ticks':5,
 'existing_piece_occurrences':42,'existing_unique_pieces':42,'new_texture_bytes':newbytes,'naive_polished_bytes':naivebytes,'dedup_saved_bytes':naivebytes-newbytes,'total_vdp1_bytes':355808+newbytes,
 'gait_source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((O/'opposite-source').glob('*.png'))},'extra_palette_bytes':0,'guide_pixels_used':guide_changes,'resources':resources,'actors':actors,'tga_sha256':newfiles,'guide_sha256':hashlib.sha256((O/'boot-edit-guide.png').read_bytes()).hexdigest()}
assert newbytes<=74688,('No texture-budget increase authorized',newbytes)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
res='\n'.join('{"%s",%d,%d,%d},'%(p['name'],p['width'],p['height'],p['aligned_bytes']) for p in resources[42:])
(R/'src/animation_polish_data.h').write_text('/* Generated byte-interned native polish resources; original 42 IDs precede these. */\n#ifndef MF_ANIMATION_POLISH_DATA_H\n#define MF_ANIMATION_POLISH_DATA_H\n#define MF_POLISH_BYTES %du\n#define MF_POLISH_NEW %d\ntypedef struct {const char *name;short width,height;unsigned bytes;} mf_polish_resource;\ntypedef struct {short resource,x,y,width,height;} mf_polish_piece;\nstatic const mf_polish_resource polish_resources[MF_POLISH_NEW]={\n%s\n};\nstatic const mf_polish_piece polish_parts[2][12][3]={\n%s\n};\nstatic const short polish_idle_ticks[2][4]={{24,16,24,16},{30,18,24,18}};\n#endif\n'%(newbytes,len(newfiles),res,',\n'.join(allparts)))
# Native and 2x comparisons always label original/polished rows distinctly.
for mode,count in [('walk',6),('idle',4)]:
 sheet=Image.new('RGB',(128*count,116*4),(27,31,43));d=ImageDraw.Draw(sheet)
 for ai,n in enumerate(['buck','chuck']):
  for version in range(2):
   row=ai*2+version
   for f in range(count):
    path=(P/f'{n}-{f+1 if mode=="walk" else 0:02d}.png') if version==0 else O/f'{n}-{f+4 if mode=="walk" else f:02d}.png'
    im=Image.open(path).convert('RGBA');x=f*128;y=row*116;sheet.paste(im,(x,y),im);d.line((x,y+92,x+127,y+92),fill=(88,112,110));d.line((x+64,y+90,x+64,y+95),fill=(130,180,150))
    d.text((x+2,y+98),f'{n} {"polish" if version else "ff24"} {f+1}',fill=(235,235,240))
 sheet.save(O/f'{mode}-compare-native.png');sheet.resize((sheet.width*2,sheet.height*2),Image.Resampling.NEAREST).save(O/f'{mode}-compare-2x.png')
print(json.dumps({k:manifest[k] for k in ['new_texture_bytes','naive_polished_bytes','dedup_saved_bytes','total_vdp1_bytes','guide_pixels_used']},indent=2));print('New unique pieces',len(newfiles),'free',458488-manifest['total_vdp1_bytes'])
