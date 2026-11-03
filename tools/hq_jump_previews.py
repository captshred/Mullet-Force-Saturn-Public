#!/usr/bin/env python3
"""Decoded native jump assemblies. Actual transitions are captured by runtime tool."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from jab_cohesion_previews import decode
from attack_sequence_previews import gif
R=Path(__file__).resolve().parents[1];O=R/'assets/hq-jump';M=json.loads((O/'manifest.json').read_text());D=[decode(O/p['name']) for p in M['resources']]
def phase(p):
 if not p.active or not p.health or p.hurt or p.torch or p.bat:return 0
 if p.height or p.vz:
  if p.attack and 3<=p.attack<=15:return 6
  if p.vz>=1362:return 1
  if -296<=p.vz<=296:return 3
  return 2 if p.vz>0 else 4
 return 5 if p.landing and not p.attack else 0

def render(actor,key,landing=6):
 n=['buck','chuck'][actor];idle=Image.open(R/f'assets/animation-polish/{n}-00.png').convert('RGBA');out=Image.new('RGBA',(160,112))
 if key==0 or (key==5 and landing<3):out.alpha_composite(idle,(0,16));return out
 if key in [1,5]:
  c=2 if key==1 else (2 if actor else 3)
  out.alpha_composite(idle.crop((0,48,128,78)),(0,66));out.alpha_composite(idle.crop((0,24,128,48)),(1 if key==1 else 0,40+c));out.alpha_composite(idle.crop((0,0,128,24)),(1 if key==1 else 0,16+c));out.alpha_composite(idle.crop((0,80,128,96)),(0,96));return out
 pose={2:0,3:1,4:2,6:3}[key]
 for q in [M['lowers'][actor][pose],M.get('extra_lowers',[[None]*4]*2)[actor][pose]]:
  if q:out.alpha_composite(D[q['resource']],(q['x'],q['y']+16))
 if key==4:out.alpha_composite(idle.crop((0,24,128,48)),(0,40))
 else:
  q=M['uppers'][actor];out.alpha_composite(D[q['resource']],(q['x'],q['y']+16))
 out.alpha_composite(idle.crop((0,0,128,24)),(0,16));return out

def main():
 for a,n in enumerate(['buck','chuck']):
  sheet=Image.new('RGBA',(7*160,128),(16,20,32,255));d=ImageDraw.Draw(sheet)
  for i,k in enumerate([0,1,2,3,4,5,6]):
   im=render(a,k);sheet.alpha_composite(im,(i*160,0));d.text((i*160+2,114),['GUARD','TAKEOFF','ASCENT','APEX','DESCENT','LAND','KICK'][i],fill='white');im.save(O/f'{n}-pose-{k}.png')
  for z in [1,4]:sheet.resize((sheet.width*z,sheet.height*z),Image.Resampling.NEAREST).save(O/f'{n}-contact-{z}x.png')
  initial=Image.open(O/'initial-comparison-1x.png').crop((a*640,0,a*640+640,128));comparison=Image.new('RGBA',(1120,256),(16,20,32,255));comparison.alpha_composite(initial);comparison.alpha_composite(sheet,(0,128))
  for z in [1,4]:comparison.resize((comparison.width*z,comparison.height*z),Image.Resampling.NEAREST).save(O/f'{n}-before-after-{z}x.png')
  both=Image.new('RGBA',(7*160,240),(16,20,32,255))
  for i,k in enumerate([0,1,2,3,4,5,6]):
   im=render(a,k);both.alpha_composite(im,(i*160,0));both.alpha_composite(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(i*160,128))
  for z in [1,4]:both.resize((both.width*z,both.height*z),Image.Resampling.NEAREST).save(O/f'{n}-both-facing-{z}x.png')
  # Offline physical-trajectory reference; actual input-driven GIFs are separate.
  for kick in [False,True]:
   seq=[];h=0;v=1510;land=0
   for t in range(56):
    if t<42:
     h+=v;v-=74
     if h<=0:h=v=0;land=6
    elif land:land-=1
    key=1 if v>=1362 else 3 if -296<=v<=296 and h else 2 if v>0 else 4 if h else 5 if land else 0
    if kick and 9<=t<=21 and h:key=6
    im=Image.new('RGBA',(192,208),(16,20,32,255));dr=ImageDraw.Draw(im);dr.line((0,190,191,190),fill=(70,80,95));dr.ellipse((47,187,91,192),fill=(5,8,14));im.alpha_composite(render(a,key,land),(0,82-h//256));seq.append(im)
   for z in [1,4]:gif(O/f'{n}-{"aerial-kick" if kick else "jump-cycle"}-composite-{z}x.gif',seq,[20 if i%3 else 10 for i in range(len(seq))],z)
 # Aerial bat remains the complete existing assembly, deliberately not reskinned.
 b=json.loads((R/'assets/bat-frames.json').read_text())
 for a,n in enumerate(['buck','chuck']):
  sheet=Image.new('RGBA',(7*160,128),(16,20,32,255))
  for f in range(7):
   meta=b[n][f];low=b['air_legs'][b['air_lower_for_frame'][f]]
   for p in [low,meta]:sheet.alpha_composite(decode(R/'assets/cd'/p['name']),(f*160+64-p['anchor'][0],108-p['anchor'][1]))
  for z in [1,4]:sheet.resize((sheet.width*z,sheet.height*z),Image.Resampling.NEAREST).save(O/f'{n}-preserved-aerial-bat-{z}x.png')
if __name__=='__main__':main()
