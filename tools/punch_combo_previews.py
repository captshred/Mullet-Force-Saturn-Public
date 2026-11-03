"""Native indexed cross with original lower; offline previews, not gameplay."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from jab_cohesion_previews import decode,render as jab
from fast_bat_previews import strike,gif
R=Path(__file__).resolve().parents[1];O=R/'assets/punch-combo'
def cross(a,t=6,flip=False):
 if t<=11:
  im=strike(a);im.paste((0,0,0,0),(0,0,160,64));im.alpha_composite(decode(O/f'XC{a}.TGA'),(40,20))
 else:im=jab(a,13 if t<=20 else 20)
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im

def main():
 for a,n in enumerate(['buck','chuck']):
  for flip in [False,True]:
   #12t jab ->12t jab ->28t cross, with physical input shown separately in runtime GIFs.
   seq=[jab(a,t) for t in range(1,13)]*2+[cross(a,t) for t in range(1,29)]+[jab(a,20)]*12
   if flip:seq=[q.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for q in seq]
   for z in [1,4]:gif(O/f'{n}-jab-jab-cross-{("left" if flip else "right")}-offline-{z}x.gif',seq,z)
  sh=Image.new('RGBA',(320,136),(16,20,32,255));sh.alpha_composite(jab(a,6));sh.alpha_composite(cross(a),(160,0));d=ImageDraw.Draw(sh);d.text((2,115),'LEAD JAB / 24t',fill='white');d.text((162,115),'REAR CROSS / 28t',fill='white')
  close=Image.new('RGBA',(320,128),(16,20,32,255));close.alpha_composite(jab(a,6).crop((40,20,120,64)).resize((160,88),Image.Resampling.NEAREST));close.alpha_composite(cross(a).crop((40,20,120,64)).resize((160,88),Image.Resampling.NEAREST),(160,0));ImageDraw.Draw(close).text((2,95),'JAB              REAR ARM ACROSS CHEST',fill='white')
  for z in [1,4]:sh.resize((320*z,136*z),Image.Resampling.NEAREST).save(O/f'{n}-jab-cross-contact-{z}x.png');close.resize((320*z,128*z),Image.Resampling.NEAREST).save(O/f'{n}-rear-arm-closeup-{z}x.png')
  cross(a).save(O/f'{n}-cross-native.png');cross(a).resize((640,448),Image.Resampling.NEAREST).save(O/f'{n}-cross-review-4x.png')
 print('Native/4x,mirrored combo cycles,jab-versus-cross contacts and arm closeups generated.')
if __name__=='__main__':main()
