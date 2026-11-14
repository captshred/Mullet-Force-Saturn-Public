#!/usr/bin/env python3
"""Match native rendered backgrounds, not late camera telemetry, at both review views."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,struct,json,argparse
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);a=p.parse_args();D=R/'docs/intersection-facade-seal';D.mkdir(exist_ok=True)
pal=np.array([0,*struct.unpack('>255H',(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())]);colors=np.stack([(pal&31)*255//31,((pal>>5)&31)*2*255//63,((pal>>10)&31)*255//31],-1).astype('uint8');old=np.frombuffer((R/'art/intersection-facade-seal/before.bin').read_bytes(),np.uint8).reshape(240,640);prefix=np.frombuffer((R/'assets/level1-neon-strip/NSPIX.BIN').read_bytes(),np.uint8).reshape(240,1280);source=np.concatenate((prefix,old),axis=1);report={}
for name,target in [('first-building',1208),('receding-street',1468)]:
 all_found=[]
 for run in (a.before,a.after):
  b=(run/'captures/trace.bin').read_bytes();found={}
  for i in range(0,len(b),144):
   t=struct.unpack_from('<36I',b,i)
   if not target-24<=t[1]<=target+24:continue
   if not (run/'captures'/f'frame-{t[0]:04}.ppm').exists():continue
   frame=Image.open(run/'captures'/f'frame-{t[0]:04}.ppm').convert('RGB');pixels=np.array(frame)[76:130]
   scores=[]
   for origin in range(target-20,target+21):
    z=source[75:129,origin:origin+320];mask=(z!=0)&~((z>=240)&(z<=247));score=np.all(colors[z]==pixels,axis=2)[mask].mean();scores.append((float(score),origin))
   score,origin=max(scores)
   if score>.65 and (origin not in found or score>found[origin][0]):found[origin]=(score,t,frame)
  all_found.append(found)
 common=all_found[0].keys()&all_found[1].keys();assert common,name;origin=min(common,key=lambda v:(abs(v-target),v));frames=[];details=[]
 for label,found in zip(('before','after'),all_found):
  score,t,frame=found[origin];frame.save(D/(name+'-'+label+'.png'));frames.append(frame);details.append(dict(frame=t[0],telemetry_camera=t[1],static_match=score))
 out=Image.new('RGB',(1280,504),(16,20,30));draw=ImageDraw.Draw(out)
 for j,im in enumerate(frames):out.paste(im.resize((640,480),Image.Resampling.NEAREST),(j*640,24));draw.text((j*640+5,5),('Before' if j==0 else 'After')+f' - camera {origin+1}',fill='white')
 out.save(D/(name+'-before-after.png'));report[name]=dict(camera=origin+1,rendered_world_origin=origin,frames=details)
 boxes=[('wall-detail',(70,0,140,60))] if name=='first-building' else [('left-walls',(48,10,105,58)),('right-walls',(155,0,231,59)),('one-moon',(104,0,180,56))]
 for label,box in boxes:
  w=(box[2]-box[0])*5;h=(box[3]-box[1])*5;out=Image.new('RGB',(w*2,h+24),(16,20,30));draw=ImageDraw.Draw(out)
  for j,im in enumerate(frames):out.paste(im.crop(box).resize((w,h),Image.Resampling.NEAREST),(j*w,24));draw.text((j*w+4,5),'Before' if j==0 else 'After',fill='white')
  out.save(D/(label+'-before-after.png'))
(D/'matched-cameras.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
