#!/usr/bin/env python3
"""Render existing indexed fragments at coordinated native joint offsets. No art edits."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,struct,hashlib
from attack_sequence_previews import render as old_render,state as old_state,gif
R=Path(__file__).resolve().parents[1];O=R/'assets/jab-cohesion';M=json.loads((R/'assets/attack-sequence/manifest.json').read_text());P=json.loads((R/'assets/animation-polish/manifest.json').read_text())
OFFSETS=[[[[2,1],[1,1],[1,1],[1,0],[0,0]],[[3,2],[2,1],[1,1],[1,0],[0,0]]],[[[1,1],[1,1],[1,1],[1,0],[0,0]],[[2,1],[1,1],[1,1],[1,0],[0,0]]]]
def decode(path):
 b=path.read_bytes();w,h=struct.unpack_from('<HH',b,12);pal=b[18:786];raw=b[786:];im=Image.new('RGBA',(w,h));im.putdata([(*pal[3*i:3*i+3][::-1],255) if i else (0,0,0,0) for y in range(h) for i in raw[(h-1-y)*w:(h-y)*w]]);return im
IMAGES=[decode(R/'assets/attack-sequence'/p['name']) for p in M['resources']]
def render(actor,t,bat=False,phase=0):
 if bat:
  if t>=18:return old_render(actor,-1)
  key,w=old_state(t,True,phase);return old_render(actor,key,w,phase)
 if t>16:return old_render(actor,-1)
 out=Image.new('RGBA',(160,112))
 if t>=11:
  name=['buck','chuck'][actor];idle=Image.open(R/f'assets/animation-polish/{name}-00.png');parts=P['actors'][actor]['frames'][0]['parts']
  for i,p in enumerate(parts):
   dx=1 if i<2 else 0;dy=0;box=(p['x'],p['y'],p['x']+p['width'],p['y']+p['height']);out.alpha_composite(idle.crop(box),(p['x']+dx,p['y']+16+dy))
  return out
 impact=int(t>=6);layers=[]
 for upper,parts in [(False,M['lowers'][actor]),(True,M['frames'][actor][0])]:
  for p in parts:
   group=(0 if p['y']<48 else 1) if upper else (2 if p['y']<80 else 3 if p['y']<96 else 4);dx,dy=OFFSETS[actor][impact][group];depth=(-1 if upper else 0)-int(upper and group==1 or not upper and group>=3);layers.append((depth,p,dx,dy))
 for depth,p,dx,dy in sorted(layers,key=lambda v:-v[0]):out.alpha_composite(IMAGES[p['resource']],(p['x']+dx,p['y']+dy))
 return out

def main():
 O.mkdir(exist_ok=True);report=dict(parent='a7e1d0522cca2d47ca0f73534955db457906ee7e',offsets=OFFSETS,recovery_offset=[1,0],texture_bytes=457632,free_bytes=856,texture_slots=229,added_texture_bytes=0,added_palette_bytes=0,added_game_bytes=16,buffer_ticks=6,earliest_restart_counter=13,elapsed_repeat_ticks=12)
 for a,name in enumerate(['buck','chuck']):
  images=[old_render(a,-1),render(a,2),render(a,6),render(a,13),render(a,20)];labels=['GUARD','EXTENSION','IMPACT','RECOVERY','GUARD'];sheet=Image.new('RGBA',(800,128),(16,20,32,255));d=ImageDraw.Draw(sheet)
  for i,im in enumerate(images):sheet.alpha_composite(im,(i*160,0));d.text((i*160+2,114),labels[i],fill='white');im.save(O/f'{name}-pose-{i}.png')
  sheet.save(O/f'{name}-contact-native.png');sheet.resize((3200,512),Image.Resampling.NEAREST).save(O/f'{name}-contact-4x.png')
  old=[old_render(a,0) if t<=10 else old_render(a,-1) for t in range(1,25)];new=[render(a,t) for t in range(1,25)];times=[20 if t%3 else 10 for t in range(24)]
  compare=[]
  for before,after in zip(old,new):
   im=Image.new('RGBA',(320,128),(16,20,32,255));im.alpha_composite(before);im.alpha_composite(after,(160,0));ImageDraw.Draw(im).text((3,114),'BEFORE                COORDINATED',fill='white');compare.append(im)
  for z in [1,4]:
   gif(O/f'{name}-single-jab-{z}x.gif',new,times,z);gif(O/f'{name}-before-after-{z}x.gif',compare,times,z)
   standing=[render(a,t,True,0) for t in range(1,37)];gif(O/f'{name}-standing-bat-{z}x.gif',standing,[20 if t%3 else 10 for t in range(36)],z)
   run=[];durations=[]
   for f in range(4):
    im=Image.new('RGBA',(176,112));im.alpha_composite(Image.open(R/f'assets/running-bat-visual/{name}-run-{f}.png'),(0,16));run.append(im);durations.append(100)
   distance=0
   for t in range(1,37):
    if t<=8:distance+=398*(9-t)//8
    im=Image.new('RGBA',(176,112));im.alpha_composite(render(a,t,True,3),(distance//256,0));run.append(im);durations.append(20 if t%3 else 10)
   gif(O/f'{name}-running-bat-{z}x.gif',run,durations,z)
 (O/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
