#!/usr/bin/env python3
"""Compare unmodified emulator frames at the same camera nearest the user capture."""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,struct,json
import numpy as np
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);a=p.parse_args();D=R/'docs/intersection-window-opacity';D.mkdir(exist_ok=True);runs=[a.before,a.after];rows=[]
for run in runs:
 b=(run/'captures/trace.bin').read_bytes();rows.append([struct.unpack_from('<36I',b,i) for i in range(0,len(b),144)])
# Telemetry is sampled after retro_run, while video may precede its last game
# update. Match the actual rendered origin against an unchanged opaque facade,
# rather than assuming the telemetry camera belongs to that video callback.
pal=np.array([0,*struct.unpack('>255H',(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())]);colors=np.stack([(pal&31)*255//31,((pal>>5)&31)*2*255//63,((pal>>10)&31)*255//31],-1).astype('uint8')
source=np.frombuffer((R/'art/intersection-window-opacity/before.bin').read_bytes(),np.uint8).reshape(240,640)
matched=[]
for run,rr in zip(runs,rows):
 found={}
 for t in rr:
  if t[0]%4 or not 1460<=t[1]<=1478:continue
  frame=Image.open(run/'captures'/f'frame-{t[0]:04}.ppm').convert('RGB');pixels=np.array(frame)[76:106,:50]
  for origin in range(1464,1473):
   region=source[75:105,origin-1280:origin-1280+50];static=(region!=0)&~((region>=240)&(region<=247))
   if np.all(np.all(colors[region]==pixels,axis=2)[static]):found.setdefault(origin,(t,frame))
 matched.append(found)
common=matched[0].keys()&matched[1].keys();assert common;cam=min(common,key=lambda v:(abs(v-1468),v));chosen=[];telemetry=[]
for name,found in zip(('before','after'),matched):
 t,im=found[cam];chosen.append(t[0]);telemetry.append(t[1]);im.save(D/(name+'.png'))
ims=[Image.open(D/(name+'.png')).convert('RGB') for name in ('before','after')]
canvas=Image.new('RGB',(1280,504),(16,20,30));dr=ImageDraw.Draw(canvas)
for i,im in enumerate(ims):canvas.paste(im.resize((640,480),Image.Resampling.NEAREST),(i*640,24));dr.text((i*640+5,5),('Approved before' if i==0 else 'Window-opacity correction')+f' - camera {cam+1}',fill='white')
canvas.save(D/'native-before-after.png')
for name,box in [('left-windows',(1518-cam,18,1557-cam,57)),('right-windows',(1648-cam,0,1696-cam,57))]:
 w=(box[2]-box[0])*7;h=(box[3]-box[1])*7;out=Image.new('RGB',(w*2,h+24),(16,20,30));dr=ImageDraw.Draw(out)
 for i,im in enumerate(ims):out.paste(im.crop(box).resize((w,h),Image.Resampling.NEAREST),(i*w,24));dr.text((i*w+4,5),'Before' if i==0 else 'After',fill='white')
 out.save(D/(name+'-before-after.png'))
(D/'matched-camera.json').write_text(json.dumps(dict(camera=cam+1,rendered_world_origin=cam,before_frame=chosen[0],after_frame=chosen[1],telemetry_cameras=telemetry,rendered_origin_verification="Exact static RGB565 facade pixel match; accounts for video/telemetry callback timing",before_source='e270d2dd8461475185be6eac503ce0c0f874974b',scope='Native production Yabause cold-start traversal, physical controller input; matching camera, actors/time may differ; no RAM writes or composited screenshots'),indent=2)+'\n')
print('Matched native camera:',cam,chosen)

# Supplemental source-level rendering removes HUD/actors only for easier review.
# Decode the unchanged hardware skyline map at the same quarter-speed scroll.
sky_cells=(R/'assets/city-gameplay-parallax/LCSKY.BIN').read_bytes();sky_map=struct.unpack('>8192H',(R/'assets/city-gameplay-parallax/LCMAP.BIN').read_bytes());sky=np.zeros((240,320),np.uint8)
for y in range(1,56):
 for x in range(1,320):
  sx=x+(cam+1)//4-1;sy=y-1;word=sky_map[(sx//512)*4096+(sy//8)*64+(sx%512)//8];tile=((word&4095)-512)//2;sky[y,x]=sky_cells[tile*64+(sy%8)*8+sx%8]
backgrounds=[]
for name in ('before','after'):
 data=source if name=='before' else np.frombuffer((R/'assets/level1-intersection/EXTPIX.BIN').read_bytes(),np.uint8).reshape(240,640)
 viewport=np.zeros((240,320),np.uint8);viewport[1:,1:]=data[:239,cam-1280+1:cam-1280+320];viewport=np.where(viewport==0,sky,viewport);image=Image.fromarray(colors[viewport]);backgrounds.append(image);image.save(D/('background-only-'+name+'.png'))
out=Image.new('RGB',(1280,504),(16,20,30));draw=ImageDraw.Draw(out)
for i,image in enumerate(backgrounds):out.paste(image.resize((640,480),Image.Resampling.NEAREST),(i*640,24));draw.text((i*640+4,5),('Before' if i==0 else 'After')+' - source/map rendering, camera '+str(cam+1)+' (HUD/actors omitted)',fill='white')
out.save(D/'background-only-before-after.png')
for name,box in [('source-left',(50,18,90,57)),('source-right',(178,0,228,57))]:
 w=(box[2]-box[0])*7;h=(box[3]-box[1])*7;out=Image.new('RGB',(w*2,h+24),(16,20,30));draw=ImageDraw.Draw(out)
 for i,image in enumerate(backgrounds):out.paste(image.crop(box).resize((w,h),Image.Resampling.NEAREST),(i*w,24));draw.text((i*w+4,5),'Before' if i==0 else 'After',fill='white')
 out.save(D/(name+'-before-after.png'))
