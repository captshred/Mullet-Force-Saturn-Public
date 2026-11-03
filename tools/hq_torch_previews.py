#!/usr/bin/env python3
"""Decoded runtime composites, not emulator captures."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from jab_cohesion_previews import decode,render as jab
from attack_sequence_previews import gif
R=Path(__file__).resolve().parents[1];O=R/'assets/hq-torch';M=json.loads((O/'manifest.json').read_text())
D=[decode(O/p['name']) for p in M['resources']]
def render(actor,pose,walk=-1,flame=0,flip=False):
 n=['buck','chuck'][actor];im=Image.new('RGBA',(192,112));idle=Image.open(R/f'assets/animation-polish/{n}-00.png').convert('RGBA');lower=idle
 if walk>=0:
  # Source matching AB/AC resources; apply approved knee-lift override for pose1.
  pm=json.loads((R/'assets/animation-study/manifest.json').read_text());lower=Image.new('RGBA',(128,96))
  for part in pm['actors'][actor]['frames'][walk+1]['parts']:
   path=R/'assets/knee-lift/overrides'/part['name'];path=path if path.exists() else R/'assets/animation-study'/part['name'];lower.alpha_composite(decode(path),(part['x'],part['y']))
 im.alpha_composite(lower.crop((0,48,128,96)),(0,64));im.alpha_composite(idle.crop((0,0,128,24)),(0,16))
 for p in M['parts'][actor][pose]:im.alpha_composite(D[p['resource']],(p['x'],p['y']+16))
 if pose==1 and flame is not None:
  fx=decode(R/f'assets/cd/FL{flame}.TGA');im.alpha_composite(fx,(64+33,108-41))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im

def main():
 for a,n in enumerate(['buck','chuck']):
  sheet=Image.new('RGBA',(6*192,128),(16,20,32,255));d=ImageDraw.Draw(sheet);oldmeta=json.loads((R/'assets/torch-frames.json').read_text());lo=json.loads((R/'assets/normal-lowers.json').read_text())
  for f in range(3):
   old=Image.new('RGBA',(192,112))
   for p in [lo[0],oldmeta[n][f]]:old.alpha_composite(decode(R/'assets/cd'/p['name']),(64-p['anchor'][0],108-p['anchor'][1]))
   if f==1:old.alpha_composite(decode(R/'assets/cd/FL0.TGA'),(97,67))
   for col,im in [(f,old),(f+3,render(a,f))]:sheet.alpha_composite(im,(col*192,0));d.text((col*192+2,114),('LEGACY ' if col<3 else 'HQ ')+['EQUIP','FIRE','PUT AWAY'][f],fill='white')
  for f in range(3):render(a,f,flame=None).save(O/f'{n}-decoded-native-{f}.png')
  for z in [1,4]:
   sheet.resize((sheet.width*z,sheet.height*z),Image.Resampling.NEAREST).save(O/f'{n}-before-after-{z}x.png')
   guard=Image.new('RGBA',(192,112));guard.alpha_composite(Image.open(R/f'assets/animation-polish/{n}-00.png'),(0,16))
   gif(O/f'{n}-equip-{z}x.gif',[guard,render(a,0),render(a,1)],[200,100,300],z)
   gif(O/f'{n}-firing-{z}x.gif',[render(a,1,flame=i) for i in range(4)],[50]*4,z)
   gif(O/f'{n}-put-away-{z}x.gif',[render(a,1),render(a,2),guard],[200,133,300],z)
   gif(O/f'{n}-strafe-{z}x.gif',[render(a,1,i//10%3,i//3%4) for i in range(30)],[20 if i%3 else 10 for i in range(30)],z)
   both=Image.new('RGBA',(384,112));both.alpha_composite(render(a,1));both.alpha_composite(render(a,1,flip=True),(192,0));both.resize((384*z,112*z),Image.Resampling.NEAREST).save(O/f'{n}-both-facing-{z}x.png')
 # Required initial comparison includes current HQ combat and original effects.
 top=Image.open(O/'original-torch-native.png');hq=Image.open(O/'current-hq-references-native.png');comp=Image.new('RGBA',(1152,384),(16,20,32,255));comp.alpha_composite(top,(0,0));comp.alpha_composite(hq,(0,128))
 for i in range(4):comp.alpha_composite(decode(R/f'assets/cd/FL{i}.TGA'),(i*192,256))
 for z in [1,4]:comp.resize((comp.width*z,comp.height*z),Image.Resampling.NEAREST).save(O/f'initial-comparison-{z}x.png')
if __name__=='__main__':main()
