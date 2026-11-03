"""Offline indexed enemy assembly; runtime captures are produced separately."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from jab_cohesion_previews import decode
R=Path(__file__).resolve().parents[1];O=R/'assets/corporate-punk-hq-combat';B=R/'assets/corporate-punk-lighting';M=json.loads((O/'manifest.json').read_text());CP=json.loads((B/'manifest.json').read_text());D=[decode(B/p['name']) for p in CP['resources']]+[decode(O/p['name']) for p in M['resources']]
def pieces(pose):
 if pose<6:return CP['poses'][pose]['parts']
 if pose==6:return [dict(p,x=p['x']-int(i<2)) for i,p in enumerate(CP['poses'][0]['parts'])]
 if pose==7:return [M['parts']['strike'] if i==1 else p for i,p in enumerate(CP['poses'][0]['parts'])]
 return [M['parts'][['hurt','fall','ground'][pose-8]]]
def render(pose,flip=False):
 q=Image.new('RGBA',(144,112))
 if pose<0:return q
 for p in pieces(pose):
  tile=D[p['resource']];tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else tile
  q.alpha_composite(tile,(112-p['x']-p['width'] if flip else 16+p['x'],16+p['y']))
 return q
# Exact runtime pose selection; no added simulation state.
def pose(e,idle=0,actor=0):
 if e.state==1:return 0 if idle<24 else 1 if idle<36 else 2
 if e.state==2:return 3+e.walk//7%3
 if e.state==3:return 0 if e.timer>16 else 6
 if e.state==4:return 7
 if e.state==5:return 7 if e.timer==36+actor*12 else 6 if e.timer>28 else 0
 if e.state==6:return 8
 if e.state==7:return 8 if e.timer>25 else 9 if e.timer>12 else 10
 return -1

def savegif(name,seq):
 for z in [1,4]:
  ims=[]
  for p in seq:
   q=Image.new('RGBA',(144,112),(16,20,30,255));q.alpha_composite(render(p));ims.append(q.resize((144*z,112*z),Image.Resampling.NEAREST).convert('RGB'))
  ims[0].save(O/f'{name}-offline-{z}x.gif',save_all=True,append_images=ims[1:],duration=[20 if i%3 else 10 for i in range(len(ims))],loop=0)

def main():
 for i,n in enumerate(['idle-0','idle-1','idle-2','walk-0','walk-1','walk-2','windup','strike','hurt-knockback','fall','ground']):
  for z in [1,4]:render(i).resize((144*z,112*z),Image.Resampling.NEAREST).save(O/f'{n}-preview-{z}x.png')
 labels=['idle-0','idle-1','idle-2','walk-0','walk-1','walk-2','windup','strike','hurt-knockback','fall','ground']
 sheet=Image.new('RGBA',(144*len(labels),256),(16,20,30,255));d=ImageDraw.Draw(sheet)
 anchors=json.loads((R/'assets/art-frames.json').read_text()) if (R/'assets/art-frames.json').exists() else None
 for i,n in enumerate(labels):
  im=render(i);sheet.alpha_composite(im,(i*144,128));d.text((i*144,242),'HQ '+n,fill='white')
  if i<6:old=render(i)
  else:
   idx=[6,7,9,10,11][i-6];tile=decode(R/f'assets/cd/EN{idx:02}.TGA');old=Image.new('RGBA',(144,112));# old texture rectangles are cropped to original anchors
   import re
   text=(R/'src/art_data.h').read_text();rows=re.search(r'enemy_anchor\[.*?=\s*\{(.*?)\};',text,re.S).group(1);ax,ay=map(int,re.findall(r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*\}',rows)[idx]);old.alpha_composite(tile,(64-ax,108-ay-1))
  sheet.alpha_composite(old,(i*144,0));d.text((i*144,114),'BEFORE '+n,fill='white')
 for z in [1,4]:sheet.resize((sheet.width*z,sheet.height*z),Image.Resampling.NEAREST).save(O/f'before-after-{z}x.png')
 both=Image.new('RGBA',(144*len(labels),256),(16,20,30,255));d=ImageDraw.Draw(both)
 for i,n in enumerate(labels):both.alpha_composite(render(i),(i*144,0));both.alpha_composite(render(i,True),(i*144,128));d.text((i*144,114),n,fill='white')
 for z in [1,4]:both.resize((both.width*z,both.height*z),Image.Resampling.NEAREST).save(O/f'both-facing-{z}x.png')
 for name,seq in [('idle',[0]*24+[1]*12+[2]*18),('walk',[3]*7+[4]*7+[5]*7),('attack',[0]*8+[6]*16+[7]*6+[6]*7+[0]*28),('hurt',[0]*6+[8]*18+[0]*24),('knockback',[0]*6+[8]*18+[0]*24),('death',[8]*5+[9]*13+[10]*12+[-1]*30)]:savegif(name,seq)
if __name__=='__main__':main()
