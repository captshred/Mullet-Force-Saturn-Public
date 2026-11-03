#!/usr/bin/env python3
"""Native assembly + observed bat-tip overlays; right-facing CCW, mirror reversed."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,math
R=Path(__file__).resolve().parents[1];O=R/'assets/attack-sequence';m=json.loads((O/'manifest.json').read_text());rv=json.loads((R/'assets/running-bat-visual/manifest.json').read_text());carry=Image.open(R/'assets/running-bat-visual/carry-native.png').convert('RGBA')
def state(t,bat=True,phase=0):
 if not bat:return (0,-1) if t<=10 else (-1,-1)
 if t<7:return 4+phase,0 if t<3 else 1 if t<5 else 2
 return (2,-1) if t<12 else (1,-1) if t<18 else (3,-1)
def render(actor,key,weapon=-1,phase=0):
 name=['buck','chuck'][actor];im=Image.new('RGBA',(160,112))
 if key<0:im=Image.new('RGBA',(160,112));im.alpha_composite(Image.open(R/f'assets/animation-polish/{name}-00.png'),(0,16));return im
 if weapon>=0:
  hx,hy=rv['hands'][actor][phase]
  if weapon==0:im.alpha_composite(carry,(hx-24,hy-16))
  else:im.alpha_composite(Image.open(O/f'rear-bat-{[-180,-225][weapon-1]}.png'),(hx-40,hy-24))
 im.alpha_composite(Image.open(R/f'assets/bat-momentum/{name}-key-3.png').crop((0,64,160,112)),(0,64))
 if key>=4:
  im.alpha_composite(Image.open(R/f'assets/running/{name}-{phase}.png').crop((0,0,128,48)),(0,16))
 else:
  upper=Image.open(O/f'{name}-key-{key}.png').convert('RGBA');mask=Image.new('RGBA',(160,112));
  for p in m['frames'][actor][key]:
   # Full PNG includes planted legs; restore only the exact upper bounds.
   box=(p['x'],p['y'],p['x']+p['width'],p['y']+p['height']);mask.alpha_composite(upper.crop(box),(p['x'],p['y']))
  im.alpha_composite(mask)
 return im

def tip(im,grip,roi):
 pts=[]
 for y in range(roi[1],roi[3]):
  for x in range(roi[0],roi[2]):
   c=im.getpixel((x,y))
   if c[3] and max(c[:3])>=100 and max(c[:3])-min(c[:3])<64:pts.append((x,y))
 assert pts
 return max(pts,key=lambda p:(p[0]-grip[0])**2+(p[1]-grip[1])**2)
def gif(path,ims,times,z):
 frames=[]
 for im in ims:
  bg=Image.new('RGBA',im.size,(16,20,32,255));bg.alpha_composite(im);frames.append(bg.resize((im.width*z,im.height*z),Image.Resampling.NEAREST))
 frames[0].save(path,save_all=True,append_images=frames[1:],duration=times,loop=0,disposal=2)
def main():
 arcs=[]
 for actor,name in enumerate(['buck','chuck']):
  native=[];labels=['REAR CARRY','REAR LEFT','REAR DOWN','FORWARD DOWN','IMPACT','FOLLOW UP'];observed=[]
  for key,weapon in [(4,0),(4,1),(4,2),(2,-1),(1,-1),(3,-1)]:native.append(render(actor,key,weapon))
  hx,hy=rv['hands'][actor][0];grips=[(hx,hy+16)]*3+[(83,62),(95 if actor==0 else 99,49 if actor==0 else 50),(77,44)]
  rois=[None,None,None,(90,62,125,88),(108,40,145,60),(82,3,114,39)]
  for f,im in enumerate(native):
   grip=grips[f]
   if f<3:
    weapon=carry if not f else Image.open(O/f'rear-bat-{[-180,-225][f-1]}.png');p=(24,32) if not f else (40,40);pts=[(x,y) for y in range(weapon.height) for x in range(weapon.width) if weapon.getpixel((x,y))[3]];q=max(pts,key=lambda z:(z[0]-p[0])**2+(z[1]-p[1])**2);end=(grip[0]+q[0]-p[0],grip[1]+q[1]-p[1])
   else:end=tip(im,grip,rois[f])
   angle=math.degrees(math.atan2(end[1]-grip[1],end[0]-grip[0]));
   if observed:
    while angle>=observed[-1]['angle']:angle-=360
   observed.append(dict(label=labels[f],grip=list(grip),tip=list(end),angle=angle,length=math.hypot(end[0]-grip[0],end[1]-grip[1])))
  sheet=Image.new('RGBA',(960,144),(16,20,32,255));draw=ImageDraw.Draw(sheet)
  for f,im in enumerate(native):
   sheet.alpha_composite(im,(f*160,0));a=observed[f];draw.line((a['grip'][0]+f*160,a['grip'][1],a['tip'][0]+f*160,a['tip'][1]),fill=(0,240,240),width=1);draw.ellipse((a['tip'][0]+f*160-2,a['tip'][1]-2,a['tip'][0]+f*160+2,a['tip'][1]+2),fill=(255,80,80));draw.text((f*160+2,114),labels[f],fill='white');draw.text((f*160+2,126),str(round(a['angle']))+' DEG',fill='cyan')
  clean=Image.new('RGBA',(960,128),(16,20,32,255));cd=ImageDraw.Draw(clean)
  for f,im in enumerate(native):clean.alpha_composite(im,(f*160,0));cd.text((f*160+2,114),labels[f],fill='white')
  clean.save(O/f'{name}-bat-contact-native.png');clean.resize((3840,512),Image.Resampling.NEAREST).save(O/f'{name}-bat-contact-4x.png')
  sheet.save(O/f'{name}-arc-overlay-native.png');sheet.resize((3840,576),Image.Resampling.NEAREST).save(O/f'{name}-arc-overlay-4x.png');arcs.append(observed)
  # Immediate jab versus previous opposite-arm chamber, same total24 ticks.
  after=[render(actor,*state(t,False)) for t in range(1,25)];before=[]
  for t in range(1,25):
   key=None if t<3 or t>=16 else 0 if t<6 or t>10 else 1
   if key is None:im=render(actor,-1)
   else:im=Image.open(R/f'assets/bat-momentum/{name}-key-{key}.png').convert('RGBA')
   before.append(im)
  compare=[]
  for a,b in zip(before,after):
   im=Image.new('RGBA',(320,128),(16,20,32,255));im.alpha_composite(a);im.alpha_composite(b,(160,0));ImageDraw.Draw(im).text((3,114),'BEFORE                AFTER: JAB',fill='white');compare.append(im)
  for z in [1,4]:
   gif(O/f'{name}-punch-before-after-{z}x.gif',compare,[20 if i%3 else 10 for i in range(24)],z)
   standing=[render(actor,*state(t),phase=0) for t in range(1,37)];gif(O/f'{name}-standing-bat-{z}x.gif',standing,[20 if i%3 else 10 for i in range(36)],z)
   moving=[];times=[]
   for f in range(4):
    im=Image.new('RGBA',(176,112));im.alpha_composite(Image.open(R/f'assets/running-bat-visual/{name}-run-{f}.png'),(0,16));moving.append(im);times.append(100)
   distance=0
   for t in range(1,37):
    if t<=8:distance+=398*(9-t)//8
    key,weapon=state(t,True,3);im=Image.new('RGBA',(176,112));im.alpha_composite(render(actor,key,weapon,3),(distance//256,0));moving.append(im);times.append(20 if t%3 else 10)
   moving.append(Image.new('RGBA',(176,112)));moving[-1].alpha_composite(render(actor,-1),(distance//256,0));times.append(200)
   gif(O/f'{name}-running-to-bat-{z}x.gif',moving,times,z)
 (O/'arc-observations.json').write_text(json.dumps(arcs,indent=2)+'\n')
 print('Observed counterclockwise bat angles:',[[round(x['angle']) for x in a] for a in arcs])

if __name__=='__main__':main()
