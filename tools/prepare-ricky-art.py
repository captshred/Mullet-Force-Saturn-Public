#!/usr/bin/env python3
"""Convert the reviewed authoritative sheet with locked masks/scales/anchors.
Rose/shoulder edits live in source artwork; no gameplay overlay or new textures.
Unedited runtime pixels retain their exact baseline RGB555 color and alpha.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,struct
from scipy.ndimage import binary_closing,binary_fill_holes,label
R=Path(__file__).resolve().parents[1];O=R/'assets/ricky';O.mkdir(exist_ok=True)
source=R/'Ricky_HQ_Animation_Sheet.png';im=Image.open(source).convert('RGB')
# box, common group scale, root X in source, source ground Y.
rows=[('idle',[(352,12,479,191,416,188),(481,15,597,191,538,188),(600,13,722,191,658,188)],.49),
('walk',[(888,13,987,184,945,184),(989,13,1072,184,1033,184),(1065,12,1163,184,1125,184),(1165,12,1254,183,1212,183),(1240,13,1337,184,1316,184),(1337,13,1458,184,1407,184)],.49),
('punch',[(336,248,452,433,400,430),(452,253,600,433,511,430),(596,251,721,433,659,430)],.48),
('chain',[(885,256,1015,431,949,431),(1013,229,1165,436,1081,432),(1134,219,1291,436,1217,432),(1263,254,1525,436,1341,432)],.48),
('jump',[(345,544,447,673,395,670),(460,464,582,624,520,670)],.49),
('hurt',[(731,500,853,671,799,668),(856,541,960,671,901,668)],.49),
('death',[(1039,536,1190,668,1117,668),(1189,571,1354,670,1265,667),(1357,618,1525,668,1438,668)],.49),
('turn',[(373,719,510,947,437,947),(505,718,642,947,572,947)],.37)]
reference=R/'art/ricky/runtime-original'
baseline=json.loads((R/'art/ricky/manifest.original.json').read_text())
edit_mask=Image.open(R/'art/ricky/rose-edit-mask.png').convert('L')
frames=[];native=[];native_masks=[]
for group,boxes,scale in rows:
 for index,v in enumerate(boxes):
  x0,y0,x1,y1,root,ground=v;rgb=np.array(im.crop((x0,y0,x1,y1)));bright=rgb.max(axis=2)>32
  # Purple presentation floors touch boots in the sheet. Remove only that
  # hue at the ground band, before component selection, never recolor pixels.
  band=max(0,min(y1-y0,ground-y0-7))
  purple=(rgb[:,:,0].astype(int)>rgb[:,:,1].astype(int)*1.35)&(rgb[:,:,2].astype(int)>rgb[:,:,1].astype(int)*1.35)
  bright[band:]&=~purple[band:]
  # Black background is flood-transparent; close the source's 1px outline gaps
  # before retaining enclosed ink. Legs remain separated because floor is cut.
  closed=binary_closing(bright,structure=np.ones((3,3)))
  components,n=label(closed);sizes=np.bincount(components.ravel());sizes[0]=0
  mask=components==int(sizes.argmax())
  filled=binary_fill_holes(mask)
  # Chain's open loop/arc is transparent, not a filled black silhouette.
  if group=='chain' and index==1:
   filled[:,max(0,1129-x0):]=mask[:,max(0,1129-x0):]
   poly=[(1013,229),(1156,229),(1156,248),(1153,254),(1164,261),(1164,300),(1135,300),(1135,436),(1013,436)]
  elif group=='chain' and index==2:
   filled[:max(0,290-y0),:]=mask[:max(0,290-y0),:]
   poly=[(1159,219),(1291,219),(1291,310),(1285,436),(1134,436),(1134,290),(1152,265),(1164,260)]
  elif group=='chain' and index==3:
   filled[:,max(0,1380-x0):]=mask[:,max(0,1380-x0):];poly=None
  else:poly=None
  if poly:
   q=Image.new('1',(x1-x0,y1-y0));ImageDraw.Draw(q).polygon([(x-x0,y-y0) for x,y in poly],fill=1);filled&=np.asarray(q)
  rgba=Image.fromarray(rgb).convert('RGBA');rgba.putalpha(Image.fromarray((filled*255).astype('uint8')))
  # All frames in a row share one scale; crouch/airborne/fall retain their
  # relative height. Turn row was depicted larger and is registered to 84px.
  w=max(1,round(rgba.width*scale));h=max(1,round(rgba.height*scale));rgba=rgba.resize((w,h),Image.Resampling.NEAREST)
  box=rgba.getbbox();assert box
  q=rgba.crop(box);pw=(q.width+7)&~7;out=Image.new('RGBA',(pw,q.height));out.alpha_composite(q)
  anchor_x=round((root-x0)*scale)-box[0];anchor_y=round((ground-y0)*scale)-box[1]
  name=f'{group}-{index}';native.append(out)
  edited=edit_mask.crop((x0,y0,x1,y1)).resize((w,h),Image.Resampling.NEAREST).crop(box)
  padded_mask=Image.new('L',out.size);padded_mask.paste(edited,(0,0));native_masks.append(np.array(padded_mask)>0)
  if group=='jump':
   # New weapon silhouettes use fixed pre-existing allocation/registration.
   original=baseline['frames'][len(frames)]
   alpha=Image.open(R/'art/ricky/jump-chain/source-alpha.png').convert('L').crop((x0,y0,x1,y1))
   authored=im.crop((x0,y0,x1,y1)).convert('RGBA');authored.putalpha(alpha)
   authored=authored.resize((w,h),Image.Resampling.NEAREST)
   left=round((root-x0)*scale)-original['anchor'][0];top=round((ground-y0)*scale)-original['anchor'][1]
   out=authored.crop((left,top,left+original['width'],top+original['height']))
   pw=out.width;q=out;anchor_x,anchor_y=original['anchor']
   native[-1]=out;native_masks[-1]=np.ones((out.height,out.width),dtype=bool)
  original=baseline['frames'][len(frames)]
  assert (name,pw,q.height,[anchor_x,anchor_y])==(original['name'],original['width'],original['height'],original['anchor'])
  frames.append(dict(name=name,source_box=list(v[:4]),scale=scale,root=[root,ground],width=pw,height=q.height,anchor=[anchor_x,anchor_y],bytes=(pw*q.height+31)&~31))
# Keep the approved palette's RGB555 colors. Reclaim redundant RGB555 entries
# for tattoo inks instead of globally requantizing clothing/chain/skin.
bgr=(reference/'RK00.TGA').read_bytes()[18:786]
palette=[v for i in range(0,768,3) for v in bgr[i:i+3][::-1]]
remap=list(range(256));seen={};free=[]
for index in range(1,255):
 red,green,blue=palette[index*3:index*3+3]
 word=(red>>3)|((green>>3)<<5)|((blue>>3)<<10)
 if word in seen:remap[index]=seen[word];free.append(index)
 else:seen[word]=index
inks=[(80,8,24),(128,8,24),(192,24,40),(232,48,56),(248,96,96),
      (16,56,24),(24,104,40),(48,152,64),(88,184,88),(24,16,24)]
assert len(free)>=len(inks),'no palette capacity without degrading original colors'
for index,color in zip(free,inks):palette[index*3:index*3+3]=color
# Reserve raw index 0 for key. Match only entries 1..254 (Jo adds one; raw 255 would wrap to transparency), no dithering.
p=np.array(palette,dtype=np.int32).reshape(256,3);unique={};ids=[]
display=[]
for number,(f,q,edited) in enumerate(zip(frames,native,native_masks)):
 a=np.array(q);data=[];old=(reference/f'RK{number:02}.TGA').read_bytes()[786:]
 for y,row in enumerate(a):
  for x,pixel in enumerate(row):
   before=old[y*q.width+x]
   if f['name'].startswith('jump-'):
    data.append(0 if pixel[3]<128 else int(np.argmin(((p[1:255]-pixel[:3].astype('int32'))**2).sum(axis=1)))+1)
   elif not before:data.append(0) # Exact original transparency/silhouette lock.
   elif not edited[y,x]:data.append(remap[before])
   else:data.append(int(np.argmin(((p[1:255]-pixel[:3].astype('int32'))**2).sum(axis=1)))+1)
 # Preview the actual RGB555 runtime payload, not unquantized authoring pixels.
 rgba=[]
 for index in data:
  if not index:rgba.append((0,0,0,0))
  else:rgba.append(tuple(((c>>3)*255)//31 for c in palette[3*index:3*index+3])+(255,))
 shown=Image.new('RGBA',q.size);shown.putdata(rgba);shown.save(O/(f['name']+'.png'));display.append(shown)
 raw=bytes(data);key=(q.width,q.height,raw)
 if key not in unique:
  ident=len(unique);unique[key]=ident
  header=bytearray(18);header[1]=1;header[2]=1;header[5:7]=struct.pack('<H',256);header[7]=24;header[12:16]=struct.pack('<HH',q.width,q.height);header[16]=8;header[17]=32
  bgr=b''.join(bytes(palette[i:i+3][::-1]) for i in range(0,768,3));(O/f'RK{ident:02}.TGA').write_bytes(header+bgr+raw)
 f['resource']=unique[key];f['decoded_sha256']=hashlib.sha256(bytes(0 if v==0 else (v+1)&255 for v in data)).hexdigest();ids.append(f['resource'])
(O/'palette.bgr24').write_bytes(b''.join(bytes(palette[i:i+3][::-1]) for i in range(0,768,3)))
manifest=dict(source=str(source.relative_to(R)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),frames=frames,definitions=len(unique),texture_bytes=sum((w*h+31)&~31 for w,h,raw in unique),reserve=49152)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
canvas=Image.new('RGB',(900,((len(native)+5)//6)*140),(35,45,48));d=ImageDraw.Draw(canvas)
for i,(q,f) in enumerate(zip(display,frames)):
 x=i%6*150;y=i//6*140;d.text((x+3,y+3),f['name'],fill='white');q=q.resize((q.width,q.height),Image.Resampling.NEAREST);canvas.paste(q,(x+12,y+125-f['anchor'][1]),q)
canvas.save(O/'atlas.png');print(json.dumps({k:manifest[k] for k in ('definitions','texture_bytes')}))

# Generate the native metadata and CRAM words from this exact conversion.
budget='#ifndef MF_RICKY_BUDGET_H\n#define MF_RICKY_BUDGET_H\n#define MF_RICKY_DEFS %d\n#define MF_RICKY_BYTES %du\n#endif\n'%(manifest['definitions'],manifest['texture_bytes'])
(R/'src/ricky_budget.h').write_text(budget)
h='/* Generated by tools/prepare-ricky-art.py. */\n#ifndef MF_RICKY_DATA_H\n#define MF_RICKY_DATA_H\n#include "ricky_budget.h"\ntypedef struct {short width,height,ax,ay;} mf_ricky_frame;\nstatic const mf_ricky_frame mf_ricky_frames[25]={\n'
for f in frames:h+='    {%d,%d,%d,%d}, /* %s */\n'%(f['width'],f['height'],*f['anchor'],f['name'])
h+='};\nstatic const unsigned short mf_ricky_colors[255]={\n'
for i in range(255):
 red,green,blue=palette[3*i:3*i+3];h+='0x%04x,'% (0x8000|(red>>3)|((green>>3)<<5)|((blue>>3)<<10))
 if i%12==11:h+='\n'
h+='\n};\n#endif\n';(R/'src/ricky_data.h').write_text(h)
