#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,re,hashlib
from jab_cohesion_previews import render,OFFSETS
R=Path(__file__).resolve().parents[1]
def validate_jab(root=R):
 o=root/'assets/jab-cohesion';m=json.loads((o/'manifest.json').read_text());text=(root/'src/jab_visual.h').read_text();literal=re.search(r'jab_offsets[^=]*=\s*({.*?});',text,re.S).group(1);parsed=json.loads(literal.replace('{','[').replace('}',']'));assert parsed==OFFSETS==m['offsets']
 for a,name in enumerate(['buck','chuck']):
  original=Image.open(root/f'assets/attack-sequence/{name}-key-0.png').convert('RGBA');foot=original.crop((0,96,160,112))
  for t in [2,6,13,20]:
   im=render(a,t);assert im.crop((0,96,160,112)).tobytes()==foot.tobytes(),(name,t,'moved boots')
   nodes={(x,y) for y in range(112) for x in range(160) if im.getpixel((x,y))[3]};components=[]
   while nodes:
    seed=nodes.pop();todo=[seed];part={seed}
    while todo:
     x,y=todo.pop()
     for dx in [-1,0,1]:
      for dy in [-1,0,1]:
       q=(x+dx,y+dy)
       if q in nodes:nodes.remove(q);part.add(q);todo.append(q)
    components.append(part)
   body=max(components,key=len)
   for box in [(40,20,100,40),(50,55,90,72),(20,96,48,110),(80,96,112,110)]:assert any(box[0]<=x<box[2] and box[1]<=y<box[3] for x,y in body),(name,t,'separated body',box)
  for phase in range(2):
   offsets=OFFSETS[a][phase];assert offsets[0]!=[0,0] and offsets[2]!=[0,0] and offsets[3]!=[0,0] and offsets[4]==[0,0];assert all(offsets[i][1]>=offsets[i+1][1] for i in range(4))
  # Removing follow-through must neither invent art nor hold the impact longer.
  for t in range(1,18):
   from attack_sequence_previews import state,render as old
   k,w=state(t,True,3);assert render(a,t,True,3).tobytes()==old(a,k,w,3).tobytes()
  for t in range(18,37):
   from attack_sequence_previews import render as old
   assert render(a,t,True,3).tobytes()==old(a,-1).tobytes()
 assert m['added_texture_bytes']==m['added_palette_bytes']==0 and m['texture_bytes']==457632 and m['free_bytes']==856 and m['texture_slots']==229
 print('PASS native jab cohesion: moved head/shoulder/waist/hips/knees, connected head-to-both-boots, grounded identical boots, existing indexed art only; bat1–17 unchanged,18–36 existing guard; no extra VDP1/palettes')
 return m
if __name__=='__main__':validate_jab()
