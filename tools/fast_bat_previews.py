"""Offline previews reconstructed from resident indexed textures; no new art."""
from pathlib import Path
from PIL import Image,ImageDraw
from run_waist_previews import run,resolve,decode,transition,SEQ
R=Path(__file__).resolve().parents[1];O=R/'assets/fast-running-bat'
def strike(a):
 im=Image.new('RGBA',(160,112))
 for p in SEQ['lowers'][a]+SEQ['frames'][a][1]:
  im.alpha_composite(decode(resolve('COMBAT/'+SEQ['resources'][p['resource']]['name'])),(p['x'],p['y']))
 return im
def render(a,t,phase=0,flip=False):
 im=Image.new('RGBA',(160,112))
 if t<4:im.alpha_composite(run(a,phase),(0,16))
 elif t<9:im=strike(a)
 else:im.alpha_composite(Image.open(R/f'assets/animation-polish/{["buck","chuck"][a]}-00.png').convert('RGBA'),(0,16))
 return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im
def gif(path,ims,z=1):
 frames=[]
 for im in ims:
  b=Image.new('RGBA',im.size,(16,20,32,255));b.alpha_composite(im);frames.append(b.resize((im.width*z,im.height*z),Image.Resampling.NEAREST).convert('RGB'))
 frames[0].save(path,save_all=True,append_images=frames[1:],duration=[20 if i%3 else 10 for i in range(len(frames))],loop=0,disposal=2)
def main():
 O.mkdir(exist_ok=True)
 for a,n in enumerate(['buck','chuck']):
  for face in [1,-1]:
   def pad(im):
    b=Image.new('RGBA',(160,112));b.alpha_composite(im,(32 if face<0 else 0,16));return b
   before=[pad(run(a,f,face<0)) for f in range(4) for _ in range(6)]
   attack=[render(a,t,3,face<0) for t in range(1,13)]
   for z in [1,4]:gif(O/f'{n}-running-bat-{("right" if face>0 else "left")}-offline-{z}x.gif',before+attack+[attack[-1]]*12,z)
  sheet=Image.new('RGBA',(480,132),(16,20,32,255));d=ImageDraw.Draw(sheet)
  for k,(t,label) in enumerate([(2,'CARRY 1-3'),(5,'CONTACT 4-8'),(10,'GUARD 9-12')]):sheet.alpha_composite(render(a,t,3),(160*k,0));d.text((160*k+2,114),label,fill='white')
  for z in [1,4]:sheet.resize((480*z,132*z),Image.Resampling.NEAREST).save(O/f'{n}-actual-pose-contact-{z}x.png')
  comparison=[]
  for t in range(1,49):
   old=transition(a,3,t) if t<=36 else render(a,12,3);new=render(a,min(t,12),3)
   im=Image.new('RGBA',(320,132),(16,20,32,255));im.alpha_composite(old);im.alpha_composite(new,(160,0));d=ImageDraw.Draw(im);d.text((2,114),'BEFORE 36t',fill='white');d.text((162,114),'AFTER 12t',fill='white');comparison.append(im)
  for z in [1,4]:gif(O/f'{n}-before-after-timing-{z}x.gif',comparison,z)
 print('Offline native/4x carry -> horizontal -> guard previews; approved run pixels untouched.')
if __name__=='__main__':main()
