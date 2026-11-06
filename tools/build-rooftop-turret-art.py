#!/usr/bin/env python3
"""Original top-down green emplacement; shared 24x24 base + eight 16x16 guns."""
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
C={'outline':(8,16,16),'base':(24,40,24),'forest':(32,64,32),'olive':(80,104,40),'edge':(136,152,72),'metal':(112,128,136),'shine':(192,208,208),'darkmetal':(48,64,64)}
base=Image.new('RGB',(24,24));d=ImageDraw.Draw(base)
d.polygon([(4,2),(19,2),(21,4),(21,19),(19,21),(4,21),(2,19),(2,4)],fill=C['outline'])
d.polygon([(5,3),(18,3),(20,5),(20,18),(18,20),(5,20),(3,18),(3,5)],fill=C['base'])
d.rectangle((5,5,18,18),fill=C['forest']);d.line((5,5,18,5),fill=C['edge']);d.line((5,6,5,17),fill=C['olive'])
d.rectangle((7,7,16,16),fill=C['olive']);d.ellipse((6,6,17,17),fill=C['outline'])
for x,y in [(5,5),(18,5),(5,18),(18,18)]:d.point((x,y),fill=C['metal'])
frames=[base];directions=[(0,7),(5,5),(7,0),(5,-5),(0,-7),(-5,-5),(-7,0),(-5,5)]
for dx,dy in directions:
 im=Image.new('RGB',(16,16));q=ImageDraw.Draw(im);end=(8+dx,8+dy)
 q.line((8,8,*end),fill=C['outline'],width=5);q.line((8,8,*end),fill=C['metal'],width=3);q.line((8,8,*end),fill=C['shine'],width=1)
 q.ellipse((3,3,12,12),fill=C['outline']);q.ellipse((4,4,11,11),fill=C['forest']);q.arc((4,4,11,11),180,300,fill=C['edge'],width=1)
 q.rectangle((6,6,9,9),fill=C['olive']);q.point((6,6),fill=C['edge']);frames.append(im)
def native(im):
 return [0 if not (r or g or b) else 0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in im.getdata()]
out='/* Original top-down olive armor and eight shared directional gun views. */\n'
for i,im in enumerate(frames):
 name='turret_base_pixels' if i==0 else 'turret_gun_%d'%(i-1)
 pixels=native(im);out+='static const unsigned short %s[%d]={\n'%(name,len(pixels))
 for row in range(im.height):out+=','.join('0x%04x'%v for v in pixels[row*im.width:(row+1)*im.width])+',\n'
 out+='};\n'
out+='static const unsigned short * const turret_gun_pixels[8]={'+','.join('turret_gun_%d'%i for i in range(8))+'};\n'
(R/'src/rooftop_turret_data.h').write_text(out)
O=R/'build/turret-review';O.mkdir(parents=True,exist_ok=True)
sheet=Image.new('RGB',(8*24,24),(8,16,24))
for i,gun in enumerate(frames[1:]):
 full=base.copy();full.paste(gun,(4,4),gun.convert('L').point(lambda p:255 if p else 0));sheet.paste(full,(i*24,0))
sheet.resize((1536,192),Image.Resampling.NEAREST).save(O/'turret-sprite-sheet.png')
print('Turret art: 1152 + 8*512 = 5248 RGB555 bytes; 9 shared definitions')
