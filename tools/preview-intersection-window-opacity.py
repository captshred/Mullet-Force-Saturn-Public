#!/usr/bin/env python3
"""Compare unmodified emulator frames at the same camera nearest the user capture."""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,struct,json
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);a=p.parse_args();D=R/'docs/intersection-window-opacity';D.mkdir(exist_ok=True);runs=[a.before,a.after];rows=[]
for run in runs:
 b=(run/'captures/trace.bin').read_bytes();rows.append([struct.unpack_from('<36I',b,i) for i in range(0,len(b),144)])
cams=[{t[1] for t in rr if t[0]%4==0 and 1464<=t[1]<=1472} for rr in rows];common=cams[0]&cams[1];assert common;cam=min(common,key=lambda v:(abs(v-1468),v));chosen=[]
for name,run,rr in zip(('before','after'),runs,rows):
 t=next(t for t in rr if t[0]%4==0 and t[1]==cam);chosen.append(t[0]);im=Image.open(run/'captures'/f'frame-{t[0]:04}.ppm').convert('RGB');im.save(D/(name+'.png'))
ims=[Image.open(D/(name+'.png')).convert('RGB') for name in ('before','after')]
canvas=Image.new('RGB',(1280,504),(16,20,30));dr=ImageDraw.Draw(canvas)
for i,im in enumerate(ims):canvas.paste(im.resize((640,480),Image.Resampling.NEAREST),(i*640,24));dr.text((i*640+5,5),('Approved before' if i==0 else 'Window-opacity correction')+f' - camera {cam}',fill='white')
canvas.save(D/'native-before-after.png')
for name,box in [('left-windows',(1518-cam,18,1557-cam,57)),('right-windows',(1648-cam,0,1696-cam,57))]:
 w=(box[2]-box[0])*7;h=(box[3]-box[1])*7;out=Image.new('RGB',(w*2,h+24),(16,20,30));dr=ImageDraw.Draw(out)
 for i,im in enumerate(ims):out.paste(im.crop(box).resize((w,h),Image.Resampling.NEAREST),(i*w,24));dr.text((i*w+4,5),'Before' if i==0 else 'After',fill='white')
 out.save(D/(name+'-before-after.png'))
(D/'matched-camera.json').write_text(json.dumps(dict(camera=cam,before_frame=chosen[0],after_frame=chosen[1],before_source='e270d2dd8461475185be6eac503ce0c0f874974b',scope='Native production Yabause cold-start traversal, physical controller input; matching camera, actors/time may differ; no RAM writes or composited screenshots'),indent=2)+'\n')
print('Matched native camera:',cam,chosen)
