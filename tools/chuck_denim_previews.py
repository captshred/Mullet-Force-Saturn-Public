"""Exact resident-piece reconstruction and nearest-neighbor review exports."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from player_death_previews import run as before_run,transition as before_transition,render as death
from player_hurt_previews import hurt
from jab_cohesion_previews import decode
R=Path(__file__).resolve().parents[1];O=R/'assets/chuck-denim-cleanup';M=json.loads((O/'manifest.json').read_text());RM=json.loads((R/'assets/running/manifest.json').read_text());SEQ=json.loads((R/'assets/attack-sequence/manifest.json').read_text());RV=json.loads((R/'assets/running-bat-visual/manifest.json').read_text())
def resolve(path):
 match=next((p for p in M['replacements'] if p['disc_path']==path),None)
 if match:return O/match['name']
 if path.startswith('COMBAT/'):
  return R/'assets/attack-sequence'/path.split('/')[-1]
 return R/'assets/running'/path

def body(f):
 im=Image.new('RGBA',(128,96))
 for k,p in enumerate(RM['actors'][1]['frames'][f]['parts']):
  name=f'RD{k}.TGA' if f==2 and k<2 else f'RN{p["resource"]-81:02}.TGA';im.alpha_composite(decode(resolve(name)),(p['x'],p['y']))
 return im

def run(a,f,flip=False):
 if a==0:return before_run(a,f,flip)
 im=Image.new('RGBA',(128,96));hx,hy=RV['hands'][a][f];im.alpha_composite(Image.open(R/'assets/running-bat-visual/carry-native.png').convert('RGBA'),(hx-24,hy-32));im.alpha_composite(body(f));return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im

def transition(a,f,t,flip=False):
 if a==0 or f<2:return before_transition(a,f,t,flip)
 from attack_sequence_previews import state,carry
 key,weapon=state(t,True,f);im=Image.new('RGBA',(160,112));hx,hy=RV['hands'][a][f]
 if weapon==0:im.alpha_composite(carry,(hx-24,hy-16))
 elif weapon>0:im.alpha_composite(Image.open(R/f'assets/attack-sequence/rear-bat-{[-180,-225][weapon-1]}.png').convert('RGBA'),(hx-40,hy-24))
 im.alpha_composite(Image.open(R/'assets/bat-momentum/chuck-key-3.png').convert('RGBA').crop((0,64,160,112)),(0,64))
 for p in SEQ['frames'][a][4+f]:
  name=f'DT{p["resource"]-51}.TGA' if f==2 and p['resource'] in [51,52] else SEQ['resources'][p['resource']]['name'];im.alpha_composite(decode(resolve('COMBAT/'+name)),(p['x'],p['y']))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im

def gif(name,ims):
 for z in [1,4]:
  frames=[]
  for im in ims:
   bg=Image.new('RGBA',im.size,(16,20,32,255));bg.alpha_composite(im);frames.append(bg.resize((bg.width*z,bg.height*z),Image.Resampling.NEAREST).convert('RGB'))
  frames[0].save(O/f'{name}-{z}x.gif',save_all=True,append_images=frames[1:],duration=[100]*len(frames),loop=0)

def main():
 for flip in [False,True]:gif('chuck-run-'+('left' if flip else 'right')+'-offline',[run(1,f,flip) for f in range(4)])
 sh=Image.new('RGBA',(512,224),(16,20,32,255));d=ImageDraw.Draw(sh)
 for f in range(4):
  sh.alpha_composite(before_run(1,f),(128*f,0));sh.alpha_composite(run(1,f),(128*f,112));d.text((128*f,98),'BEFORE '+str(f+1),fill='white');d.text((128*f,210),'CLEAN '+str(f+1),fill='white')
 for z in [1,4]:sh.resize((512*z,224*z),Image.Resampling.NEAREST).save(O/f'chuck-contact-{z}x.png')
 for f,label,box in [(2,'shoulder',(42,19,68,39)),(3,'beltline',(52,37,85,49))]:
  old=Image.open(R/'assets/player-death/chuck-run-2-final.png' if f==2 else R/'assets/running/chuck-3.png').convert('RGBA');new=body(f);diag=old.copy();d=ImageDraw.Draw(diag)
  for x,y in M['changes'][str(f)]:d.point((x,y),fill=(255,40,140,255))
  ims=[old.crop(box),diag.crop(box),new.crop(box)];w,h=ims[0].size;cell=max(w,48);sh=Image.new('RGBA',(cell*3,h+12),(16,20,32,255));d=ImageDraw.Draw(sh)
  for k,im in enumerate(ims):sh.alpha_composite(im,(k*cell+(cell-w)//2,0));d.text((k*cell+2,h),['BEFORE','MASK','AFTER'][k],fill='white')
  for z in [1,8]:sh.resize((sh.width*z,sh.height*z),Image.Resampling.NEAREST).save(O/f'frame{f+1}-{label}-before-after-{z}x.png')
if __name__=='__main__':main()
