#!/usr/bin/env python3
"""Build only the review-stage idle/walk candidates. Never runs draw-assets.py.
Source art is an image-generation study referenced to the user masters and old
pose guide. Native idle remains byte/pixel exact; no other moves are generated.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,struct
r=Path(__file__).resolve().parents[1];out=r/'assets/animation-study';out.mkdir(exist_ok=True)
source=Image.open(out/'source-walk.png').convert('RGBA');w,h=source.size
pal=(r/'assets/gallery/GB0.TGA').read_bytes()[18:786]
colors=[tuple(pal[3*i:3*i+3][::-1]) for i in range(256)]
cache={}
def nearest(c):
 if c not in cache:cache[c]=min(range(1,254),key=lambda i:sum((c[k]-colors[i][k])**2 for k in range(3)))
 return cache[c]
def indexed(im):
 return [nearest(p[:3]) if p[3]>=128 else 0 for p in im.getdata()]
def rgba(indices):
 im=Image.new('RGBA',(128,96));im.putdata([(*colors[i],255) if i else (0,0,0,0) for i in indices]);return im
actors=[];allbytes=0;files={};header=[]
for actor,name in enumerate(['Buck','Chuck']):
 approved=Image.open(r/f'assets/gallery/{name.lower()}-88.png').convert('RGBA')
 idle=Image.new('RGBA',(128,96));idle.alpha_composite(approved,(64-approved.width//2,4))
 frames=[idle];cells=[]
 band=source.crop((0,actor*h//2,w,(actor+1)*h//2));a=band.getchannel('A')
 projection=[sum(1 for v in a.crop((x,0,x+1,a.height)).getdata() if v>=128) for x in range(w)]
 cuts=[0]
 for i in range(1,6):
  target=round(i*w/6);cut=min(range(target-40,target+41),key=lambda x:(projection[x],abs(x-target)))
  assert projection[cut]==0,'Figures overlap; review source layout instead of clipping them'
  cuts.append(cut)
 cuts.append(w)
 for f in range(6):
  cell=band.crop((cuts[f],0,cuts[f+1],band.height));mask=cell.getchannel('A').point(lambda v:255 if v>=128 else 0)
  box=mask.getbbox();assert box
  crop=cell.crop(box);nw=round(crop.width*88/crop.height);assert nw<=120
  # Premultiplied-alpha Lanczos prevents RGB from transparent fringe pixels
  # bleeding into downsampled outlines. Quantization uses the fixed approved bank.
  native=crop.convert('RGBa').resize((nw,88),Image.Resampling.LANCZOS).convert('RGBA')
  im=Image.new('RGBA',(128,96));im.alpha_composite(native,(64-nw//2,4));frames.append(rgba(indexed(im)))
  cells.append({'source_cell':[cuts[f],actor*h//2,cuts[f+1],(actor+1)*h//2],'opaque_crop':list(box)})
 infos=[];partsperactor=[]
 for f,im in enumerate(frames):
  pixels=indexed(im);native=rgba(pixels)
  if f==0:assert native.tobytes()==idle.tobytes(),'Approved native idle colors must remain exact'
  native.save(out/f'{name.lower()}-{f:02d}.png')
  bbox=native.getbbox();assert bbox[1]==4 and bbox[3]==92,(name,f,bbox)
  parts=[];reconstructed=[0]*(128*96)
  for part,(top,bottom) in enumerate([(0,24),(24,80),(80,96)]):
   region=native.crop((0,top,128,bottom));box=region.getbbox();assert box
   x,y,x2,y2=box;y+=top;y2+=top;pw=((x2-x+7)//8)*8;ph=y2-y
   payload=bytes(pixels[yy*128+xx] if xx<x2 else 0 for yy in range(y2-1,y-1,-1) for xx in range(x,x+pw))
   for yy in range(ph):
    for xx in range(pw):
     val=payload[(ph-1-yy)*pw+xx]
     if val:
      i=(y+yy)*128+x+xx;assert not reconstructed[i];reconstructed[i]=val
   fn=f'A{"B" if actor==0 else "C"}{f}{part}.TGA'
   if f==0:
    fn=f'G{"B" if actor==0 else "C"}{part}.TGA'
    old=(r/'assets/gallery'/fn).read_bytes();assert old[786:]==payload
   else:
    head=bytearray(18);head[1]=1;head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,pw,ph);head[16]=8
    data=bytes(head)+pal+payload;(out/fn).write_bytes(data);files[fn]=hashlib.sha256(data).hexdigest();allbytes+=(pw*ph+31)&~31
   parts.append({'name':fn,'x':x,'y':y,'width':pw,'height':ph,'aligned_bytes':(pw*ph+31)&~31})
  assert reconstructed==pixels
  foot=[x for x in range(128) if pixels[91*128+x]]
  info={'frame':f,'pose':'approved-idle' if f==0 else ['contact-L','down-L','passing-R','contact-R','down-R','passing-L'][f-1],
        'root':[64,92],'opaque_bounds':list(bbox),'foot_pixels_y91':foot,'parts':parts,
        'rgba_sha256':hashlib.sha256(native.tobytes()).hexdigest(),'new_texture_bytes':sum(p['aligned_bytes'] for p in parts) if f else 0}
  if f:info.update(cells[f-1])
  infos.append(info);partsperactor.append('{'+','.join('{"%s",%d,%d,%d,%d}'%(p['name'],p['x'],p['y'],p['width'],p['height']) for p in parts)+'}')
 actorbytes=sum(x['new_texture_bytes'] for x in infos)
 actors.append({'name':name,'frames':infos,'new_texture_bytes':actorbytes})
 # GIF uses nearest-neighbor scaling and exact transparency. Timing is 80/80/90
 # ms twice, a 500ms approximation to six equal 5/60-second simulation holds.
 gifframes=[]
 for x in frames[1:]:
  g=Image.new('P',(128,96));g.putpalette([v for c in colors for v in c]);g.putdata(indexed(x));g.info['transparency']=0
  gifframes.append(g.resize((384,288),Image.Resampling.NEAREST))
 gifframes[0].save(out/f'{name.lower()}-walk.gif',save_all=True,append_images=gifframes[1:],duration=[80,80,90,80,80,90],loop=0,disposal=2,transparency=0,optimize=False)
 header.append('{'+','.join(partsperactor)+'}')
manifest={'status':'UNAPPROVED ART STUDY; no gameplay replacement','source_sha256':hashlib.sha256((out/'source-walk.png').read_bytes()).hexdigest(),
 'canvas':[128,96],'root':[64,92],'standing_height':88,'alpha_threshold':128,'color_indices':[1,253],'palette_sha256':hashlib.sha256(pal).hexdigest(),
 'idle_ticks':32,'walk_ticks':5,'new_texture_bytes':allbytes,'extra_palette_bytes':0,'actors':actors,'tga_sha256':files}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(r/'src/animation_data.h').write_text('/* Generated review-only native sprite pieces. Idle uses existing gallery IDs. */\n#ifndef MF_ANIMATION_DATA_H\n#define MF_ANIMATION_DATA_H\n#define MF_ANIMATION_BYTES %du\ntypedef struct {const char *name;short x,y,width,height;} mf_animation_piece;\nstatic const mf_animation_piece animation_parts[2][7][3]={\n%s\n};\n#endif\n'%(allbytes,',\n'.join(header)))
sheet=Image.new('RGB',(896,232),(27,31,43));d=ImageDraw.Draw(sheet)
for a,actor in enumerate(actors):
 for f in range(7):
  x=f*128;y=a*116;im=Image.open(out/f'{actor["name"].lower()}-{f:02d}.png').convert('RGBA');sheet.paste(im,(x,y),im)
  d.line((x,y+92,x+127,y+92),fill=(90,110,110));d.line((x+64,y+90,x+64,y+95),fill=(110,160,130))
  d.text((x+2,y+98),f'{actor["name"]} '+('idle approved' if not f else f'walk {f} / 5t'),fill=(230,235,240))
sheet.save(out/'contact-native.png');sheet.resize((1792,464),Image.Resampling.NEAREST).save(out/'contact-2x.png')
(out/'preview.html').write_text('''<!doctype html><meta charset="utf-8"><title>Mullet Force idle / walk study</title><style>body{background:#191d29;color:#eee;font:16px system-ui;max-width:1000px;margin:30px auto}canvas,img{image-rendering:pixelated;max-width:100%}button{padding:8px;margin:5px}</style><h1>Idle / walk art study — approval pending</h1><p>Approved idle pixels are unchanged. Six walk candidates per fighter; no gameplay sprites replaced. Walk: 6 × 5/60 seconds. Baseline: y=92; root x=64.</p><button id="mode">Idle / walk</button><button id="pause">Pause / play</button><button id="flip">Mirror</button><canvas id="view" width="768" height="288"></canvas><p id="label"></p><img src="contact-2x.png"><script>
const ctx=document.getElementById('view').getContext('2d');ctx.imageSmoothingEnabled=false;let walk=true,paused=false,flip=false,phase=0,last=performance.now();let frames=[[],[]];for(let a=0;a<2;a++)for(let f=0;f<7;f++){let i=new Image();i.src=['buck','chuck'][a]+'-'+String(f).padStart(2,'0')+'.png';frames[a].push(i)}document.getElementById('mode').onclick=()=>{walk=!walk;phase=0};document.getElementById('pause').onclick=()=>paused=!paused;document.getElementById('flip').onclick=()=>flip=!flip;function draw(t){if(!paused)phase+=t-last;last=t;let f=walk?1+Math.floor(phase/(1000*5/60))%6:0;ctx.fillStyle='#1b1f2b';ctx.fillRect(0,0,768,288);for(let a=0;a<2;a++){ctx.save();ctx.translate(a*384+(flip?384:0),0);ctx.scale(flip?-3:3,3);if(frames[a][f].complete)ctx.drawImage(frames[a][f],0,0);ctx.restore()}document.getElementById('label').textContent=(walk?'Walk ':'Approved idle ')+f+' —'+(paused?' paused':' playing');requestAnimationFrame(draw)}requestAnimationFrame(draw)</script>''')
print(f'Animation candidates: 36 new textures, {allbytes} bytes aligned; existing idle reused; total VDP1 {302336+allbytes}/458488.')
