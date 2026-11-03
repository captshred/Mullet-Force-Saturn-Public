"""Exact native run/prep assembly with separate development seam annotations."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from chuck_denim_previews import run as oldrun,transition as oldtransition,resolve as oldresolve
from jab_cohesion_previews import decode
R=Path(__file__).resolve().parents[1];O=R/'assets/run-waist-seam';M=json.loads((O/'manifest.json').read_text());RM=json.loads((R/'assets/running/manifest.json').read_text());SEQ=json.loads((R/'assets/attack-sequence/manifest.json').read_text());RV=json.loads((R/'assets/running-bat-visual/manifest.json').read_text())
def resolve(path):
 item=next((q for q in M['replacements'] if q['disc_path']==path),None)
 return O/item['name'] if item else oldresolve(path)
def body(a,f):
 q=Image.new('RGBA',(128,96))
 for k,p in enumerate(RM['actors'][a]['frames'][f]['parts']):
  name=f'RD{k}.TGA' if a==1 and f==2 and k<2 else f'RN{p["resource"]-81:02}.TGA';q.alpha_composite(decode(resolve(name)),(p['x'],p['y']))
 return q

def run(a,f,flip=False):
 im=Image.new('RGBA',(128,96));hx,hy=RV['hands'][a][f];im.alpha_composite(Image.open(R/'assets/running-bat-visual/carry-native.png').convert('RGBA'),(hx-24,hy-32));im.alpha_composite(body(a,f));return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im

def transition(a,f,t,flip=False):
 from attack_sequence_previews import state,carry
 key,weapon=state(t,True,f)
 if key<4:return oldtransition(a,f,t,flip)
 im=Image.new('RGBA',(160,112));hx,hy=RV['hands'][a][f]
 if weapon==0:im.alpha_composite(carry,(hx-24,hy-16))
 elif weapon>0:im.alpha_composite(Image.open(R/f'assets/attack-sequence/rear-bat-{[-180,-225][weapon-1]}.png').convert('RGBA'),(hx-40,hy-24))
 im.alpha_composite(Image.open(R/f'assets/bat-momentum/{["buck","chuck"][a]}-key-3.png').convert('RGBA').crop((0,64,160,112)),(0,64))
 for p in SEQ['frames'][a][4+f]:
  name=f'DT{p["resource"]-51}.TGA' if a==1 and f==2 and p['resource'] in [51,52] else SEQ['resources'][p['resource']]['name'];im.alpha_composite(decode(resolve('COMBAT/'+name)),(p['x'],p['y']))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im

def gif(name,ims):
 for z in [1,4]:
  out=[]
  for im in ims:
   bg=Image.new('RGBA',im.size,(16,20,32,255));bg.alpha_composite(im);out.append(bg.resize((bg.width*z,bg.height*z),Image.Resampling.NEAREST).convert('RGB'))
  out[0].save(O/f'{name}-{z}x.gif',save_all=True,append_images=out[1:],duration=[100]*len(out),loop=0)

def main():
 landmarks=[]
 for a,n in enumerate(['buck','chuck']):
  for flip in [False,True]:gif(n+'-run-'+('left' if flip else 'right')+'-offline',[run(a,f,flip) for f in range(4)])
  sheet=Image.new('RGBA',(512,224),(16,20,32,255));d=ImageDraw.Draw(sheet);close=Image.new('RGBA',(512,144),(16,20,32,255));cd=ImageDraw.Draw(close);diag=Image.new('RGBA',(512,144),(16,20,32,255));dd=ImageDraw.Draw(diag)
  for f in range(4):
   sheet.alpha_composite(oldrun(a,f),(128*f,0));sheet.alpha_composite(run(a,f),(128*f,112));d.text((128*f,98),'BEFORE '+str(f+1),fill='white');d.text((128*f,210),'AFTER '+str(f+1),fill='white')
   for i,im in enumerate([oldrun(a,f),run(a,f)]):
    crop=im.crop((44,34,88,51));bg=Image.new('RGBA',crop.size,(65,25,65,255));bg.alpha_composite(crop);close.alpha_composite(bg.resize((88,34),Image.Resampling.NEAREST),(128*f+18,8+i*62));cd.text((128*f+2,44+i*62),str(f+1)+(' BEFORE' if i==0 else ' AFTER'),fill='white')
   diag.alpha_composite(run(a,f),(128*f,0));pieces=RM['actors'][a]['frames'][f]['parts']
   for p in pieces[1:]:dd.line((128*f+24,p['y'],128*f+112,p['y']),fill='orange')
   dd.line((128*f+42,44,128*f+88,44),fill='red');landmark=(68 if a==0 else 69,43 if f%2==0 else 42);dd.ellipse((128*f+landmark[0]-1,landmark[1]-1,128*f+landmark[0]+1,landmark[1]+1),outline='cyan');dd.line((128*f+61,92,128*f+67,92),fill='yellow');dd.line((128*f+64,89,128*f+64,95),fill='yellow');dd.text((128*f+2,99),'POSE '+str(18+f)+' / DEV ONLY',fill='white');dd.text((128*f+2,111),'RED source join y44',fill='red');dd.text((128*f+2,123),'CYAN pelvis landmark',fill='cyan');dd.text((128*f+2,135),'ORANGE piece cuts',fill='orange');landmarks.append(dict(actor=a,frame=f,pelvis_landmark=list(landmark),engine_root=[64,92],piece_boundaries=[p['y'] for p in pieces[1:]],art_join_y=44))
  for z in [1,4]:
   sheet.resize((512*z,224*z),Image.Resampling.NEAREST).save(O/f'{n}-contact-{z}x.png');close.resize((512*z,144*z),Image.Resampling.NEAREST).save(O/f'{n}-waist-before-after-{z}x.png');diag.resize((512*z,144*z),Image.Resampling.NEAREST).save(O/f'{n}-seam-diagnostic-{z}x.png')
 (O/'diagnostic-landmarks.json').write_text(json.dumps(landmarks,indent=2)+'\n')
if __name__=='__main__':main()
