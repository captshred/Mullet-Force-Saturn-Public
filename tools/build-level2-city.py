#!/usr/bin/env python3
"""Deterministic native tile art: eight industrial compounds + distant skyline.
No external art/master inputs. Review PNGs stay in ignored build/.
"""
from pathlib import Path
import struct,json,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';B=R/'build/city-review';B.mkdir(parents=True,exist_ok=True)
pal=struct.unpack('>16H',(A/'WPAL.BIN').read_bytes())
rgb=[((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31) for v in pal]
def canvas(fill):
 im=Image.new('P',(512,512),fill);im.putpalette(sum((list(c) for c in rgb),[])+[0]*(768-48));return im
city=canvas(1);d=ImageDraw.Draw(city)
# Continuous street grid, quiet colors and an exact top/bottom wrap.
for x in (112,376):
 d.rectangle((x,0,x+23,511),fill=2)
 d.line((x+2,0,x+2,511),fill=4);d.line((x+21,0,x+21,511),fill=4)
 for y in range(12,512,40):d.rectangle((x+11,y,x+12,y+16),fill=7)
for y,h in ((0,8),(128,16),(256,16),(384,16),(488,24)):
 d.rectangle((0,y,511,y+h-1),fill=2)
 d.line((0,y,511,y),fill=3)
 for x in range(20,512,48):d.line((x,y+h//2,x+16,y+h//2),fill=4)
# Keep vertical wrapping edges identical rather than splitting a facade.
d.line((0,0,511,0),fill=2);d.line((0,511,511,511),fill=2)
def vent(x,y,w=18):
 d.rectangle((x,y,x+w,y+12),fill=1);d.rectangle((x+1,y+1,x+w-2,y+9),fill=5)
 for yy in range(y+3,y+9,3):d.line((x+3,yy,x+w-4,yy),fill=2)
def pipe(x,y,w,h):
 d.line((x,y,x+w,y,x+w,y+h),fill=1,width=4);d.line((x,y-1,x+w,y-1,x+w,y+h),fill=5)
 for xx in range(x+5,x+w,13):d.line((xx,y-2,xx,y+1),fill=6)
def sign(x,y,text):
 d.rectangle((x-2,y-2,x+len(text)*6,y+9),fill=1);d.text((x,y),text,fill=6)
def building(box,kind,roof=3):
 x,y,w,h=box;r=x+w-1;b=y+h-1
 d.rectangle((x+4,y+5,r+5,b+5),fill=12)
 d.rectangle((x,y,r,b),fill=4);d.rectangle((x,y,r,y+2),fill=6)
 d.rectangle((x+3,y+4,r-3,b-4),fill=roof)
 d.line((x+3,b-3,r-3,b-3),fill=2);d.line((r-2,y+3,r-2,b-3),fill=2)
 # Low-contrast grime, wall seams, boarded loading bays and narrow alleys.
 for xx in range(x+8,r-7,18):
  d.line((xx,b-2,xx+9,b-2),fill=1);d.line((xx+2,b-3,xx+7,b-3),fill=5)
 for yy in range(y+18,b-12,24):d.line((x+5,yy,r-5,yy),fill=4)
 if kind=='mill':
  vent(x+12,y+15,26);vent(x+12,y+45,26);pipe(x+49,y+17,23,h-43)
  sign(x+9,b-19,'MILL 07')
 elif kind=='sawtooth':
  for xx in range(x+8,r-12,19):
   d.polygon([(xx,y+10),(xx+14,y+4),(xx+14,b-16),(xx,b-10)],fill=2)
   d.line((xx,y+10,xx+14,y+4,xx+14,b-16),fill=5)
  d.rectangle((x+7,b-12,r-7,b-7),fill=1)
 elif kind=='boiler':
  for xx in (x+16,x+42):
   d.rectangle((xx,y+16,xx+13,y+52),fill=2);d.ellipse((xx-2,y+11,xx+15,y+27),fill=5)
   d.ellipse((xx+2,y+15,xx+11,y+23),fill=1)
  pipe(x+13,b-19,w-28,-15)
 elif kind=='ruin':
  d.polygon([(r-32,y+4),(r-24,y+20),(r-15,y+14),(r-4,y+26),(r-3,y+4)],fill=12)
  for xx,yy in ((r-25,y+11),(r-15,y+24),(r-7,y+17)):
   d.rectangle((xx,yy,xx+4,yy+3),fill=4)
  d.line((x+19,y+8,x+27,y+25,x+22,y+36,x+35,y+47),fill=1)
  for yy in range(y+25,b-18,18):
   d.rectangle((r-33,yy,r-14,yy+9),fill=1);d.line((r-33,yy,r-14,yy+8),fill=5)
  vent(x+12,b-25);sign(x+8,y+50,'DEPOT')
 elif kind=='water':
  tx=x+47;ty=y+30
  d.line((tx-12,ty+8,tx-17,ty+31),fill=1,width=3);d.line((tx+12,ty+8,tx+17,ty+31),fill=1,width=3)
  d.ellipse((tx-18,ty-18,tx+18,ty+13),fill=2);d.ellipse((tx-18,ty-22,tx+18,ty+6),fill=5)
  d.arc((tx-15,ty-19,tx+15,ty+3),190,310,fill=6);d.line((tx+22,ty-12,tx+22,ty+25),fill=6)
  vent(x+9,b-22)
 elif kind=='power':
  for xx in range(x+12,r-15,26):
   d.rectangle((xx,y+17,xx+15,b-19),fill=2)
   for yy in range(y+20,b-19,6):d.line((xx+2,yy,xx+13,yy),fill=5)
  pipe(x+12,b-12,w-26,-6);sign(x+8,y+5,'GRID')
 elif kind=='loft':
  for yy in range(y+14,b-15,16):
   d.rectangle((x+10,yy,r-9,yy+8),fill=1);d.line((x+10,yy,r-9,yy),fill=5)
  d.line((x+8,y+6,x+8,b-8),fill=5)
 elif kind=='loading':
  for xx in range(x+11,r-17,28):
   d.rectangle((xx,y+17,xx+19,b-12),fill=2)
   for yy in range(y+20,b-13,4):d.line((xx+1,yy,xx+18,yy),fill=4)
  d.rectangle((x+7,y+7,r-8,y+12),fill=5);sign(x+13,b-10,'FREIGHT')
segments=[('Rivet mill',(144,18,98,94),'mill',3),('Sawtooth foundry',(258,10,104,106),'sawtooth',4),
 ('Boiler house',(148,157,78,82),'boiler',3),('Broken rail depot',(244,153,120,88),'ruin',4),
 ('Water tower works',(144,284,96,81),'water',3),('Power substation',(256,279,108,91),'power',4),
 ('Narrow brick loft',(148,411,62,65),'loft',3),('Freight loading hall',(228,415,134,61),'loading',4)]
for name,box,kind,roof in segments:building(box,kind,roof)
for row,y in enumerate((17,155,281,412)):
 building((10,y,82,90 if row<3 else 64),('mill','loft','loading','ruin')[row],3)
 building((414,y+3,80,86 if row<3 else 60),('power','water','boiler','sawtooth')[row],3)
# Fenced yards and a few sparse alley details, away from projectile colors.
for x,y in ((230,181),(369,305),(218,429)):
 d.line((x,y,x,y+39),fill=5)
 for yy in range(y,y+40,7):d.line((x-2,yy,x+2,yy+4),fill=3)
 d.rectangle((x-5,y+44,x+1,y+49),fill=2)
# Distant upper city: independent panorama, no connected facade that can tear.
sky=canvas(0);q=ImageDraw.Draw(sky);q.rectangle((0,0,511,79),fill=1)
skysegments=[(0,35,62,'steps'),(72,26,61,'saw'),(144,34,43,'tank'),(198,21,64,'mill'),(273,35,50,'stacks'),(334,38,69,'broken'),(414,28,90,'gantry')]
for x,top,w,kind in skysegments:
 q.rectangle((x,top,x+w-1,84),fill=2);q.line((x,top,x+w-1,top),fill=4)
 if kind=='steps':q.rectangle((x+12,top-10,x+w-15,top),fill=2);q.line((x+12,top-10,x+w-15,top-10),fill=4)
 if kind=='saw':
  for xx in range(x,x+w-8,12):q.polygon([(xx,top),(xx+10,top-8),(xx+10,top)],fill=3)
 if kind=='tank':
  q.line((x+8,top-3,x+4,top+29),fill=4);q.line((x+w-8,top-3,x+w-4,top+29),fill=4)
  q.rectangle((x+6,top-21,x+w-6,top-4),fill=3);q.ellipse((x+6,top-25,x+w-6,top-15),fill=4)
 if kind=='mill':
  q.rectangle((x+16,top-8,x+w-9,top),fill=3);q.line((x+16,top-8,x+w-9,top-8),fill=4)
 if kind=='stacks':
  for xx in (x+9,x+30):q.rectangle((xx,top-26,xx+7,top+7),fill=3);q.rectangle((xx-1,top-26,xx+8,top-23),fill=4)
 if kind=='broken':q.polygon([(x+7,top),(x+18,top+10),(x+26,top+3),(x+36,top+15),(x+47,top)],fill=1)
 if kind=='gantry':
  q.line((x+12,top+5,x+12,top-14,x+w-12,top-14,x+w-12,top+5),fill=4,width=2)
  q.line((x+w-24,top-14,x+w-24,top+13),fill=3)
 for yy in range(top+12,78,12):
  for xx in range(x+8,x+w-5,13):q.rectangle((xx,yy,xx+4,yy+3),fill=3)
# Screen-space haze: opaque upper band becomes progressively transparent.
for y in range(72,104):
 for x in range(512):
  if y<80:
   if (x+2*y)%4==0:sky.putpixel((x,y),1)
  else:
   density=max(0,16*(103-y)//23)
   sky.putpixel((x,y),1 if ((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))[y%4][x%4]<density else 0)
# Never draw a hard terminal row at the bottom of the overlay.
q.line((0,103,511,103),fill=0)
def encode(im,base):
 tiles=[];lookup={};words=[]
 for ty in range(64):
  for tx in range(64):
   b=im.crop((tx*8,ty*8,tx*8+8,ty*8+8)).tobytes()
   if b not in lookup:lookup[b]=len(tiles);tiles.append(b)
   words.append(0x1000+base//32+lookup[b]*2)
 return b''.join(tiles),struct.pack('>4096H',*words)
lc,lm=encode(city,0);sc,sm=encode(sky,0x10000)
assert len(lc)<=65536 and len(sc)<=40960
for name,b in [('WCELL.BIN',lc),('WMAP.BIN',lm),('WSKY.BIN',sc),('WSMAP.BIN',sm)]: (A/name).write_bytes(b)
p=A/'manifest.json';m=json.loads(p.read_text())
for name in ['WCELL.BIN','WMAP.BIN','WSKY.BIN','WSMAP.BIN']:
 b=(A/name).read_bytes();m['files'][name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
m['tiles']=len(lc)//64;m['sky_tiles']=len(sc)//64;m['vdp2_payload_bytes']=len(lc)+len(lm)+len(sc)+len(sm)
m['city']={'width':512,'height':512,'crop_x':96,'sky_visible_height':104,'sky_rate_denominator':2,'segments':[{'name':n,'bounds':box,'style':k} for n,box,k,c in segments],'sky_segments':len(skysegments)}
p.write_text(json.dumps(m,indent=2)+'\n')
(R/'src/wingsuit_city_data.h').write_text('/* Generated by tools/build-level2-city.py; native 8bpp cell payloads. */\n#ifndef MF_WS_CITY_DATA_H\n#define MF_WS_CITY_DATA_H\n#define MF_WS_CITY_CELL_BYTES %d\n#define MF_WS_SKY_CELL_BYTES %d\n#define MF_WS_SKY_CELL_OFFSET 65536\n#define MF_WS_SKY_MAP_OFFSET 8192\n#define MF_WS_CITY_MAP_BYTES 8192\n#define MF_WS_SKY_RATE_DIVISOR 2\n#endif\n'%(len(lc),len(sc)))
city.convert('RGB').save(B/'city-map.png');sky.convert('RGB').save(B/'sky-map.png')
# Native view composites use the same origin/rate as runtime (subpixels omitted).
for camera in (0,48,96):
 for scroll in (0,96,256):
  lower=Image.new('RGB',(224,240));upper=sky.convert('RGB');mask=Image.frombytes('L',sky.size,bytes(255 if p else 0 for p in sky.tobytes()))
  for yy in range(240):lower.paste(city.crop((96+camera, (yy-scroll)%512,96+camera+224,(yy-scroll)%512+1)).convert('RGB'),(0,yy))
  sx=96+(camera-48)//2+48;lower.paste(upper.crop((sx,0,sx+224,240)),(0,0),mask.crop((sx,0,sx+224,240)))
  lower.resize((448,480),Image.Resampling.NEAREST).save(B/f'view-{camera}-{scroll}.png')
print(json.dumps({k:m[k] for k in ['tiles','sky_tiles','vdp2_payload_bytes']}))
