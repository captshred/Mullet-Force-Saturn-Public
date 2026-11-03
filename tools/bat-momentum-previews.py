#!/usr/bin/env python3
"""Exact native source compositions with true integer slide positions; no redrawing."""
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'assets/bat-momentum/review';O.mkdir(exist_ok=True)
for name in ['buck','chuck']:
 for f in [2,3]:
  old=Image.open(R/f'assets/combat-animation/{name}-key-{f}.png');new=Image.open(R/f'assets/bat-momentum/{name}-key-{f}.png');sheet=Image.new('RGBA',(320,128),(16,20,32,255));sheet.alpha_composite(old);sheet.alpha_composite(new,(160,0));d=ImageDraw.Draw(sheet);d.text((4,114),'BEFORE',fill='white');d.text((164,114),'AFTER +20 CONTACT / FIXED LEGS',fill='white');sheet.save(O/f'{name}-pose-{f}-before-after-native.png');sheet.resize((1280,512),Image.Resampling.NEAREST).save(O/f'{name}-pose-{f}-before-after-4x.png')
 sequence=[];before_sequence=[];durations=[];ground=127
 for phase in range(4):
  im=Image.new('RGBA',(208,144),(16,20,32,255));im.alpha_composite(Image.open(R/f'assets/running-bat-visual/{name}-run-{phase}.png'),(16,ground-92));ImageDraw.Draw(im).line((0,ground+1,207,ground+1),fill=(68,78,96));sequence.append(im);before_sequence.append(im.copy());durations.append(100)
 slide=0;old_slide=0
 for t in range(1,37):
  if t<=8:slide+=398*(9-t)//8;old_slide+=663
  key=2 if t<12 or t>=28 else 3
  im=Image.new('RGBA',(208,144),(16,20,32,255));im.alpha_composite(Image.open(R/f'assets/bat-momentum/{name}-key-{key}.png'),(16+slide//256,ground-108));ImageDraw.Draw(im).line((0,ground+1,207,ground+1),fill=(68,78,96));sequence.append(im)
  old=Image.new('RGBA',(208,144),(16,20,32,255))
  if t<6:old.alpha_composite(Image.open(R/f'assets/running-bat-visual/{name}-run-3.png'),(16+old_slide//256,ground-92))
  else:
   old.alpha_composite(Image.open(R/f'assets/combat-animation/{name}-key-{key}.png').crop((0,0,160,64)),(16+old_slide//256,ground-108));phase=(3+(t-6)//6)%4;old.alpha_composite(Image.open(R/f'assets/running/{name}-{phase}.png').crop((0,48,128,96)),(16+old_slide//256,ground-44))
  ImageDraw.Draw(old).line((0,ground+1,207,ground+1),fill=(68,78,96));before_sequence.append(old);durations.append(20 if t%3 else 10)
 for z in [1,4]:
  ims=[im.resize((208*z,144*z),Image.Resampling.NEAREST) for im in sequence];ims[0].save(O/f'{name}-run-plant-slide-{z}x.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2)
  ims=[]
  for old,new in zip(before_sequence,sequence):
   im=Image.new('RGBA',(416,160),(16,20,32,255));im.alpha_composite(old);im.alpha_composite(new,(208,0));d=ImageDraw.Draw(im);d.text((4,145),'BEFORE: RUNNING LEGS',fill='white');d.text((212,145),'AFTER: PLANTED SLIDE',fill='white');ims.append(im.resize((416*z,160*z),Image.Resampling.NEAREST))
  ims[0].save(O/f'{name}-comparison-{z}x.gif',save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=2)
