#!/usr/bin/env python3
"""Host path/sprite review from actual C functions; never an emulator capture."""
from pathlib import Path
import subprocess,tempfile,re
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];out=R/'build/enemy-review';out.mkdir(parents=True,exist_ok=True)
source='''#include <stdio.h>
#include "wingsuit.c"
int main(void){int p,t,i;for(t=0;t<300;t+=4)for(p=0;p<3;p++)for(i=0;i<8;i++){
 mf_ws_enemy e={.kind=MF_WS_CHROME_EYE,.pattern=p,.origin=112*256,.direction=1,.age=t-i*18};
 move_enemy(&e);printf("%d %d %d %d %d\\n",t,p,i,e.x/256,e.y/256);
}return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 c=Path(tmp)/'paths.c';exe=Path(tmp)/'paths';c.write_text(source)
 subprocess.run(['cc','-std=c99','-Isrc',str(c),'-o',str(exe)],cwd=R,check=True)
 data=subprocess.check_output([str(exe)],text=True)
(out/'paths.txt').write_text(data)
pixels=[int(v,16) for v in re.findall(r'0x[0-9a-f]{4}',(R/'src/chrome_eye_data.h').read_text())]
sprite=Image.new('RGBA',(16,16));sprite.putdata([((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31,255 if v else 0) for v in pixels])
sprite.resize((128,128),Image.Resampling.NEAREST).save(out/'chrome-eye.png')
frames=[]
records=[list(map(int,line.split())) for line in data.splitlines()]
for t in range(0,300,4):
 im=Image.new('RGB',(224*3,264),(8,16,24));d=ImageDraw.Draw(im)
 for p,title in enumerate(['S-Snake','Wide Sweep','Tight Weave']):
  d.text((p*224+8,5),title,fill=(170,210,230));d.rectangle((p*224,24,p*224+223,263),outline=(40,60,75))
 for tick,p,i,x,y in records:
  if tick==t and -8<=y<248:im.paste(sprite,(p*224+x-8,y+24-8),sprite)
 d.text((8,251),'HOST PATH REVIEW - not emulator footage',fill=(150,150,150))
 frames.append(im.resize((1344,528),Image.Resampling.NEAREST))
frames[0].save(out/'chrome-eye-paths.gif',save_all=True,append_images=frames[1:],duration=67,loop=0)
contact=Image.new('RGB',(1344,528*3))
for i,index in enumerate([20,32,44]):contact.paste(frames[index],(0,528*i))
contact.save(out/'chrome-eye-sequence.png')
print('Host review:',out)
# Drone trajectories also come from the production spawn/move functions.
source='''#include <stdio.h>
#include "wingsuit.c"
int main(void){int p,t,i;for(p=0;p<5;p++){mf_wingsuit g;mf_ws_init(&g,0);
 g.pattern_bag=1u<<p;g.spawn=1;spawn_enemies(&g);
 for(t=0;t<225;t++)for(i=0;i<3;i++){mf_ws_enemy *e=&g.enemies[i];
  if(e->delay){--e->delay;continue;}++e->age;move_enemy(e);
  printf("%d %d %d %d %d\\n",p,t,i,e->x/256-48,e->y/256);
 }}return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 c=Path(tmp)/'drones.c';exe=Path(tmp)/'drones';c.write_text(source)
 subprocess.run(['cc','-std=c99','-Isrc',str(c),'-o',str(exe)],cwd=R,check=True)
 data=subprocess.check_output([str(exe)],text=True)
im=Image.new('RGB',(224*5,264),(8,16,24));d=ImageDraw.Draw(im)
for p,title in enumerate(['Diagonal','Staggered descent','Crossing','Curved approach','Lateral sweep']):
 d.text((p*224+8,5),title,fill=(170,210,230));d.rectangle((p*224,24,p*224+223,263),outline=(40,60,75))
for row in data.splitlines():
 p,t,i,x,y=map(int,row.split())
 if 0<=y<240 and 0<=x<224:d.point((p*224+x,y+24),fill=[(90,200,230),(220,180,90),(190,100,210)][i])
d.text((8,251),'HOST TRAJECTORY REVIEW - not emulator footage',fill=(150,150,150))
im.resize((2240,528),Image.Resampling.NEAREST).save(out/'drone-paths.png')
