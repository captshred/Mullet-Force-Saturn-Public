#!/usr/bin/env python3
"""Real C simulation + native city/sprites. Host composite, not emulator footage."""
from pathlib import Path
import re,struct,subprocess,tempfile
from PIL import Image,ImageChops,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'build/turret-review';O.mkdir(parents=True,exist_ok=True)
source='''#include <stdio.h>
#include "wingsuit.c"
int main(void){mf_wingsuit g;int t,i;mf_ws_init(&g,1);g.spawn=10000;
 for(t=0;t<660;t++){
  unsigned h=t<100?MF_RIGHT:(t<260?MF_LEFT:(t<410?MF_RIGHT:MF_LEFT));
  g.players[0].invulnerable=g.players[1].invulnerable=10000;
  mf_ws_step(&g,(unsigned[2]){h,h},(unsigned[2]){0,0},3);
  if(t%4)continue;
  printf("F %d %d %d\\n",t,g.camera_x,g.scroll);
  for(i=0;i<2;i++)printf("P %d %d %d\\n",i,mf_ws_screen_x(&g,g.players[i].x)/256,g.players[i].y/256);
  for(i=0;i<2;i++){mf_ws_turret *a=&g.turrets[i];printf("T %d %d %d %d %d %d\\n",i,mf_ws_screen_x(&g,a->x)/256,a->y/256,a->visible,a->hp,a->aim);}
  for(i=0;i<4;i++)if(g.turret_shots[i].active)printf("B %d %d\\n",mf_ws_screen_x(&g,g.turret_shots[i].x)/256,g.turret_shots[i].y/256);
 }return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 c=Path(tmp)/'review.c';exe=Path(tmp)/'review';c.write_text(source)
 subprocess.run(['cc','-std=c99','-Isrc',str(c),'-o',str(exe)],cwd=R,check=True)
 data=subprocess.check_output([str(exe)],text=True)
(O/'simulation.txt').write_text(data)
def rgba(v):return ((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31,255 if v else 0)
def sprite(values,w,h):
 im=Image.new('RGBA',(w,h));im.putdata([rgba(v) for v in values]);return im
def native_sprite(n,w,h):return sprite(struct.unpack('>'+str(w*h)+'H',(R/'assets/wingsuit'/n).read_bytes()),w,h)
art=[int(v,16) for v in re.findall(r'0x[0-9a-f]{4}',(R/'src/rooftop_turret_data.h').read_text())]
base=sprite(art[:576],24,24);guns=[sprite(art[576+i*256:576+(i+1)*256],16,16) for i in range(8)]
players=[native_sprite('WBUCK.BIN',32,32),native_sprite('WCHUCK.BIN',32,32)];bullet=native_sprite('WHOST.BIN',8,8)
palette=struct.unpack('>16H',(R/'assets/wingsuit/WPAL.BIN').read_bytes())
def plane(cn,mn,offset):
 chars=(R/'assets/wingsuit'/cn).read_bytes();words=struct.unpack('>4096H',(R/'assets/wingsuit'/mn).read_bytes());im=Image.new('RGBA',(512,512))
 for ty in range(64):
  for tx in range(64):
   tile=((words[ty*64+tx]&4095)-offset//32)//2
   values=[palette[v] if v else 0 for v in chars[tile*64:tile*64+64]]
   im.paste(sprite(values,8,8),(tx*8,ty*8))
 return im
bg=plane('WCELL.BIN','WMAP.BIN',0);roof=plane('WROOF.BIN','WRMAP.BIN',65536)
frames=[];im=None;stats=[];player_draws=[]
def finish():
 if im is None:return
 for actor,x,y in player_draws:im.alpha_composite(players[actor],(x-48-16,y-16))
 framed=Image.new('RGB',(224,264),(8,16,24));framed.paste(im,(0,24));d=ImageDraw.Draw(framed)
 d.text((4,2),'HOST COMPOSITE / not emulator',fill=(170,185,190));d.text((4,13),'CAM %02d / SCROLL %03d'%(cam//256,scroll),fill=(130,160,170))
 frames.append(framed.resize((448,528),Image.Resampling.NEAREST));stats.append((tick,cam,scroll))
for line in data.splitlines():
 parts=line.split();v=list(map(int,parts[1:]))
 if parts[0]=='F':
  finish();tick,cam,scroll=v;player_draws=[]
  gx=96+cam//256;rx=(144*65536+(cam-48*256)*288)//65536
  im=ImageChops.offset(bg,0,scroll).crop((gx,0,gx+224,240));upper=ImageChops.offset(roof,0,scroll).crop((rx,0,rx+224,240));im.alpha_composite(upper)
 elif parts[0]=='T':
  i,x,y,visible,hp,aim=v
  if visible and hp:im.alpha_composite(base,(x-48-12,y-12));im.alpha_composite(guns[aim],(x-48-8,y-8))
 elif parts[0]=='P':
  i,x,y=v;player_draws.append((i,x,y))
 elif parts[0]=='B':
  x,y=v;im.alpha_composite(bullet,(x-48-4,y-4))
finish()
frames[0].save(O/'rooftop-turrets.gif',save_all=True,append_images=frames[1:],duration=67,loop=0)
contact=Image.new('RGB',(448*3,528*2))
for i,idx in enumerate([40,55,72,84,99,140]):contact.paste(frames[idx],((i%3)*448,(i//3)*528))
contact.save(O/'rooftop-turret-sequence.png')
# Full map with anchor footprints, for review of approved roof surfaces.
full=bg.copy();full.alpha_composite(roof)
for x,y in [(308,244),(343,392)]:full.alpha_composite(base,(x-12,y-12));full.alpha_composite(guns[0],(x-8,y-8))
full.resize((1024,1024),Image.Resampling.NEAREST).save(O/'rooftop-anchor-map.png')
print('Host C/native-asset review:',O)
