from pathlib import Path
from PIL import Image,ImageDraw
import json
from player_hurt_previews import hurt,run as oldrun,transition as oldtransition,R,decode
O=R/'assets/player-death';M=json.loads((O/'manifest.json').read_text())
def render(a,f,flip=False):
 if f<2:im=hurt(a,0 if f==0 else 2)
 else:
  im=Image.new('RGBA',(128,96));n=['buck','chuck'][a];im.alpha_composite(Image.open(R/f'assets/player-hurt/{n}-hurt-2.png').convert('RGBA').crop((0,0,128,52)),(0,14));p=M['lowers'][a];im.alpha_composite(decode(O/M['resources'][p['resource']]['name']),(p['x'],p['y']))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im
def run(a,f,flip=False):
 im=oldrun(a,f)
 if a==1 and f==2:
  carry=Image.open(R/'assets/running-bat-visual/carry-native.png').convert('RGBA');meta=json.loads((R/'assets/running-bat-visual/manifest.json').read_text());x,y=meta['hands'][a][f];im=Image.new('RGBA',(128,96));im.alpha_composite(carry,(x-24,y-32));im.alpha_composite(Image.open(O/'chuck-run-2-final.png').convert('RGBA'))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im
def transition(a,f,t,flip=False):
 im=oldtransition(a,f,t)
 if a==1 and f==2:
  # Replace just the registered source upper, with existing weapon/lower untouched.
  from attack_sequence_previews import state,rv,carry
  key,weapon=state(t,True,f)
  im=Image.new('RGBA',(160,112));hx,hy=rv['hands'][a][f]
  if weapon==0:im.alpha_composite(carry,(hx-24,hy-16))
  elif weapon>0:im.alpha_composite(Image.open(R/f'assets/attack-sequence/rear-bat-{[-180,-225][weapon-1]}.png'),(hx-40,hy-24))
  im.alpha_composite(Image.open(R/'assets/bat-momentum/chuck-key-3.png').crop((0,64,160,112)),(0,64));im.alpha_composite(Image.open(O/'chuck-run-2-final.png').crop((0,0,128,48)),(0,16))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im
def gif(name,ims,durations):
 for z in [1,4]:
  frames=[]
  for im in ims:
   bg=Image.new('RGBA',im.size,(16,20,32,255));bg.alpha_composite(im);frames.append(bg.resize((bg.width*z,bg.height*z),Image.Resampling.NEAREST).convert('RGB'))
  frames[0].save(O/f'{name}-{z}x.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
def main():
 for a,n in enumerate(['buck','chuck']):
  for flip in [False,True]:gif(n+'-death-'+('left' if flip else 'right')+'-offline',[render(a,f,flip) for f in range(3)],[130,270,1600])
  gif(n+'-hurt-to-death-offline',[hurt(a,f) for f in range(3)]+[render(a,f) for f in range(3)],[70,60,70,130,270,1600])
  sh=Image.new('RGBA',(512,112),(16,20,32,255));d=ImageDraw.Draw(sh)
  for f in range(3):sh.alpha_composite(render(a,f),(f*128,0));d.text((f*128,99),['A SEVERE HIT / 8t','B STAGGER / 16t','C KNEE / 96t'][f],fill='white')
  sh.alpha_composite(render(a,2,True),(384,0));d.text((384,99),'C MIRRORED',fill='white')
  for z in [1,4]:sh.resize((512*z,112*z),Image.Resampling.NEAREST).save(O/f'{n}-death-contact-{z}x.png')
 for flip in [False,True]:gif('chuck-run-'+('left' if flip else 'right')+'-offline',[run(1,f,flip) for f in range(4)],[100]*4)
 old=Image.open(R/'assets/player-hurt/chuck-run-2-clean.png').convert('RGBA');new=Image.open(O/'chuck-run-2-final.png').convert('RGBA');diag=old.copy();d=ImageDraw.Draw(diag)
 for p in json.loads((O/'source/run-strip-changed-pixels.json').read_text()):d.point(tuple(p),fill=(255,40,140,255))
 sh=Image.new('RGBA',(384,112),(16,20,32,255));d=ImageDraw.Draw(sh)
 for i,(im,label) in enumerate([(old,'BEFORE'),(diag,'DEV PATCH MASK'),(new,'FINAL')]):sh.alpha_composite(im,(128*i,0));d.text((128*i,99),label,fill='white')
 for z in [1,4]:sh.resize((384*z,112*z),Image.Resampling.NEAREST).save(O/f'chuck-frame3-before-after-{z}x.png')
 sh=Image.new('RGBA',(512,112),(16,20,32,255));d=ImageDraw.Draw(sh)
 for f in range(4):sh.alpha_composite(run(1,f),(f*128,0));d.text((f*128,99),f'FRAME {f+1} SAME HAND',fill='white')
 for z in [1,4]:sh.resize((512*z,112*z),Image.Resampling.NEAREST).save(O/f'chuck-bat-hand-contact-{z}x.png')
if __name__=='__main__':main()
