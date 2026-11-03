#!/usr/bin/env python3
"""Offline localized animation edits, fixed approved palette, deduplicated bands."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,struct
R=Path(__file__).resolve().parents[1];A=R/'assets/corporate-punk-animation';M=R/'assets/corporate-punk';A.mkdir(exist_ok=True)
master=Image.open(M/'corporate-punk-84.png');pal=(M/'palette.bgr24').read_bytes();rgba=master.convert('RGBA');guide=Image.open(A/'source/animation-edit-guide.png').convert('RGBA')
colors={i:tuple(pal[3*i:3*i+3][::-1]) for i in sorted(set(master.getdata())-{0})}
def indexed(im):
 q=Image.new('P',(96,96));q.putpalette(master.getpalette());q.putdata([min(colors,key=lambda i:sum((p[k]-colors[i][k])**2 for k in range(3))) if p[3]>=192 else 0 for p in im.getdata()]);q.info['transparency']=0;return q
# Import only local edit regions from registered guide cells. Face/hair/body
# and all untouched pixels remain the exact approved indexed raster.
def registered(cell):
 q=guide.crop((cell*guide.width//5,0,(cell+1)*guide.width//5,guide.height));q.putalpha(q.getchannel('A').point(lambda v:255 if v>=192 else 0));q=q.crop(q.getbbox());q=q.resize((round(q.width*84/q.height),84),Image.Resampling.NEAREST)
 pts=[x for y in range(12) for x in range(q.width) if q.getpixel((x,y))[3]];cx=sum(pts)//len(pts)
 out=Image.new('RGBA',(96,96));out.alpha_composite(q,(58-cx,8))
 # Discard isolated guide-edge specks; keep the connected fighter silhouette.
 seen=set()
 for yy in range(96):
  for xx in range(96):
   if (xx,yy) in seen or not out.getpixel((xx,yy))[3]:continue
   todo=[(xx,yy)];component=[];seen.add((xx,yy))
   while todo:
    px,py=todo.pop();component.append((px,py))
    for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
     if 0<=nx<96 and 0<=ny<96 and (nx,ny) not in seen and out.getpixel((nx,ny))[3]:seen.add((nx,ny));todo.append((nx,ny))
   if len(component)<=3:
    for point in component:out.putpixel(point,(0,0,0,0))
 return out
frames=[master.copy()]
# Restrained shoulder and fist changes from first two edited guide cells.
# Two compact regions, maximum one-pixel envelope; feet/head untouched.
for cell in [0,1]:
 q=rgba.copy();v=registered(cell)
 for box in [(33,24,43,32),(65,33,70,40)]:
  x0,y0,x1,y1=box
  for y in range(y0,y1):
   for x in range(x0,x1):
    p=v.getpixel((x,y));old=rgba.getpixel((x,y))
    if old[3] and p[3]:q.putpixel((x,y),p)
 frames.append(indexed(q))
# Short-step guides are imported below the fixed pelvis only. Middle pose is
# the exact approved weight-transfer stance, sharing every band with idle1.
for cell in [2,None,3]:
 q=rgba.copy()
 if cell is not None:
  v=registered(cell)
  for y in range(49,92):
   for x in range(96):q.putpixel((x,y),v.getpixel((x,y)))
 frames.append(indexed(q))
for old in A.glob('CP*.TGA'):old.unlink()
names=['idle-0','idle-1','idle-2','walk-0','walk-1','walk-2'];resources=[];lookup={};poses=[]
for name,q in zip(names,frames):
 q.save(A/f'{name}.png',transparency=0);raw=bytes(q.getdata());parts=[]
 # Fixed bands preserve the exact approved three-piece idle construction.
 for top,bottom in [(8,20),(20,76),(76,92)]:
  box=q.convert('RGBA').crop((0,top,96,bottom)).getbbox();x,y,x2,y2=box;x2=(x2-x+7)//8*8+x;y+=top;y2+=top
  # Even band origins/heights maintain the existing SGL sprite raster convention.
  if y%2:y-=1
  if (y2-y)%2:y2+=1
  w,h=x2-x,y2-y;payload=bytes(raw[yy*96+xx] if 0<=xx<96 else 0 for yy in range(y2-1,y-1,-1) for xx in range(x,x2));key=(w,h,payload)
  if key not in lookup:
   rid=len(resources);lookup[key]=rid;filename=f'CP{rid:02d}.TGA';head=bytearray(18);head[1]=head[2]=1;struct.pack_into('<H',head,5,256);head[7]=24;struct.pack_into('<HH',head,12,w,h);head[16]=8
   (A/filename).write_bytes(bytes(head)+pal+payload);resources.append({'name':filename,'width':w,'height':h,'bytes':(w*h+31)&~31,'sha256':hashlib.sha256((A/filename).read_bytes()).hexdigest()})
  parts.append({'resource':lookup[key],'x':x,'y':y,'width':w,'height':h})
 poses.append({'name':name,'parts':parts})
for label,group,durations in [('idle',frames[:3],[400,200,300]),('walk',frames[3:],[120,120,120])]:
 ims=[q.convert('RGBA').resize((384,384),Image.Resampling.NEAREST) for q in group];ims[0].save(A/f'{label}-4x.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2,transparency=0)
sheet=Image.new('RGBA',(576,112),(27,31,43,255));d=ImageDraw.Draw(sheet)
for i,(n,q) in enumerate(zip(names,frames)):sheet.alpha_composite(q.convert('RGBA'),(96*i,0));d.text((96*i+2,99),n,fill='white')
sheet.save(A/'contact-native.png');sheet.resize((2304,448),Image.Resampling.NEAREST).save(A/'contact-4x.png')
total=sum(r['bytes'] for r in resources);m={'approved_commit':'c25d00c15805149273c5ef8ab8f33f54d920b2dd','canvas':[96,96],'root':[48,92],'palette':'../corporate-punk/palette.bgr24','resources':resources,'poses':poses,'texture_bytes':total,'texture_slots':len(resources),'idle_holds':[24,12,18],'walk_holds':[7,7,7],'boot_bytes':351104+total,'boot_free':458488-351104-total,'full_bytes':427104+total,'full_free':458488-427104-total,'boot_slots':125+len(resources)}
(A/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
h=['/* Offline-generated shared enemy artwork. No gameplay state. */','#ifndef MF_CORPORATE_DATA_H','#define MF_CORPORATE_DATA_H',f'#define MF_CP_TEXTURE_BYTES {total}u',f'#define MF_CP_RESOURCES {len(resources)}','typedef struct {const char *name;short width,height;} mf_cp_resource;','typedef struct {short resource,x,y,width;} mf_cp_piece;','static const mf_cp_resource cp_resources[]={']
h += [' {"%s",%d,%d},'%(r['name'],r['width'],r['height']) for r in resources];h+=['};','static const mf_cp_piece cp_poses[6][3]={'];h += [' {'+','.join('{%d,%d,%d,%d}'%(p['resource'],p['x'],p['y'],p['width']) for p in pose['parts'])+'},' for pose in poses];h+=['};','#endif'];(R/'src/corporate_data.h').write_text('\n'.join(h)+'\n');print(json.dumps({k:m[k] for k in ['texture_bytes','texture_slots','boot_bytes','boot_free','full_free','boot_slots']}))
