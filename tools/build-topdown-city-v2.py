#!/usr/bin/env python3
"""Original aerial pixel architecture, native indexed cells, no reference pixels.
Six sites over three city blocks. Tall buildings are COMPLETE cutouts, including
walls, equipment and shadows; their empty ground plots allow +/-6px parallax.
"""
from pathlib import Path
import json,struct,hashlib
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1];A=R/'assets/wingsuit';O=R/'build/topdown-v2-review';O.mkdir(parents=True,exist_ok=True)
palette=struct.unpack('>16H',(A/'WPAL.BIN').read_bytes());rgb=[((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31) for v in palette]
def canvas(fill):
 im=Image.new('P',(512,512),fill);im.putpalette(sum((list(c) for c in rgb),[])+[0]*(768-48));return im
base=canvas(1);raised=canvas(0);d=ImageDraw.Draw(base)
# Same street axes and 512px vertical period as the approved city. Sidewalks,
# crossings, storm drains and broad unpainted alleys make the blocks believable.
for x in (112,376):
 d.rectangle((x-3,0,x+26,511),fill=3);d.rectangle((x,0,x+23,511),fill=12)
 for y in range(12,512,32):d.line((x+11,y,x+11,y+11),fill=7)
for top,bottom in ((0,7),(144,163),(320,339),(488,511)):
 d.rectangle((0,top,511,bottom),fill=12)
 for x in range(0,512,40):d.line((x+7,(top+bottom)//2,x+22,(top+bottom)//2),fill=4)
 for x in (112,376):
  for y in range(top+3,bottom-1,4):d.rectangle((x+3,y,x+20,y+1),fill=5)
# Smooth the wrap without a sliced structure or changing scroll timing.
d.line((0,0,511,0),fill=12);d.line((0,511,511,511),fill=12)
for ya,yb in ((8,139),(168,315),(344,483)):
 d.rounded_rectangle((139,ya,373,yb),radius=5,fill=13,outline=4)
 d.line((142,ya+7,142,yb-5),fill=2)
 for yy in range(ya+16,yb-4,24):
  d.line((140,yy,143,yy),fill=5);d.line((369,yy,372,yy),fill=5)
 for xx in range(151,367,32):d.line((xx,yb-2,xx+13,yb-2),fill=2)
for x in (118,382):
 for y in (132,308,476):
  d.rectangle((x,y,x+10,y+3),fill=1)
  for xx in range(x+1,x+10,3):d.line((xx,y,xx,y+2),fill=4)

def body(layer,points,height,roof=3,material="concrete"):
 q=ImageDraw.Draw(layer);xs=[p[0] for p in points];ys=[p[1] for p in points]
 # Every shadow and wall stays with this building's roof on the same plane.
 q.polygon([(x+5,y+height+3) for x,y in points],fill=12)
 q.polygon([(x,y+height) for x,y in points],fill=2)
 for (x,y),(xx,yy) in zip(points,points[1:]+points[:1]):
  if y==yy and xx<x:
   for wx in range(xx+4,x-2,8):q.rectangle((wx,y+2,wx+4,y+height-1),fill=8)
 q.polygon(points,fill=6)
 mask=Image.new('L',(512,512));ImageDraw.Draw(mask).polygon(points,fill=255)
 for kernel,color in ((3,2),(5,5),(7,4),(11,roof)):
  inset=mask.filter(ImageFilter.MinFilter(kernel));layer.paste(color,(0,0),inset)
 # Repeated sparse concrete wear, masked inside parapets, is deliberately
 # low-contrast and tile-friendly rather than high-frequency random noise.
 inner=mask.filter(ImageFilter.MinFilter(15));wear=Image.new('P',layer.size,roof);w=ImageDraw.Draw(wear)
 for y in range(min(ys)+9,max(ys)-8):
  for x in range(min(xs)+9,max(xs)-8):
   if material=='metal':
    if x%12==0:wear.putpixel((x,y),2)
    elif x%12==1:wear.putpixel((x,y),4)
    if y%40==0:wear.putpixel((x,y),4)
   elif ((x%8)*13+(y%8)*7)%64==0:wear.putpixel((x,y),4 if roof!=4 else 3)
 for y in range(min(ys)+19,max(ys)-10,31):
  for x in range(min(xs)+17,max(xs)-10,37):
   w.polygon([(x,y),(x+12,y),(x+9,y+3),(x+5,y+3),(x+5,y+6),(x,y+6)],fill=3 if roof==4 else 2)
   w.point((x+15,y+9),fill=4)
 layer.paste(wear,(0,0),inner)
 return q

def fan(q,x,y,n=18):
 q.rectangle((x+2,y+3,x+n+2,y+n+3),fill=12);q.rectangle((x,y,x+n,y+n),fill=5)
 q.rectangle((x+2,y+2,x+n-2,y+n-2),fill=2)
 q.ellipse((x+3,y+3,x+n-3,y+n-3),fill=1,outline=4)
 c=x+n//2;v=y+n//2
 q.line((c-4,v-3,c+4,v+3),fill=5,width=2);q.line((c-3,v+4,c+3,v-4),fill=5,width=2)
 q.ellipse((c-1,v-1,c+1,v+1),fill=6)
def tank(q,x,y,r):
 q.ellipse((x-r+2,y-r+3,x+r+2,y+r+3),fill=12)
 q.ellipse((x-r,y-r,x+r,y+r),fill=2,outline=5)
 q.ellipse((x-r+3,y-r+3,x+r-3,y+r-3),fill=4,outline=3)
 q.arc((x-r+4,y-r+4,x+r-4,y+r-4),200,300,fill=6)
 q.ellipse((x-2,y-2,x+2,y+2),fill=5)
def duct(q,points):
 q.line([(x+1,y+2) for x,y in points],fill=12,width=5);q.line(points,fill=5,width=3);q.line(points,fill=4)
def hatch(q,x,y,w=16,h=14):
 q.rectangle((x+2,y+3,x+w+2,y+h+3),fill=12);q.rectangle((x,y,x+w,y+h),fill=5)
 q.rectangle((x+2,y+2,x+w-2,y+h-2),fill=3);q.line((x+4,y+5,x+w-4,y+5),fill=6)
def grating(q,x,y,w,h):
 q.rectangle((x,y,x+w,y+h),fill=2,outline=5)
 for xx in range(x+3,x+w,4):q.line((xx,y+2,xx,y+h-2),fill=4)
 for yy in range(y+4,y+h,6):q.line((x+2,yy,x+w-2,yy),fill=3)

sites=[]
def site(name,shape,height,plane,yard=None,roof=3,material="concrete"):
 layer=raised if plane else base;q=body(layer,shape,height,roof,material)
 sites.append({'name':name,'plane':plane,'footprint':shape,'wall_height':height,'yard':yard})
 return q
# Two buildings per block, with distinctly different silhouettes; none is a
# front elevation or a detached decoration band.
q=site('Dockworks: bevelled broad warehouse',[(156,16),(258,16),(258,58),(270,58),(270,126),(146,126),(146,30)],4,0,roof=4)
hatch(q,157,29,21,17);tank(q,227,45,14);fan(q,160,76);fan(q,190,76)
duct(q,[(168,101),(214,101),(214,78),(244,78)]);grating(q,233,91,22,20)
q.line((187,34,187,59,201,59),fill=5);q.line((151,117,258,117),fill=2)
# Faded roof stencil, not an upright sign.
q.text((193,110),'D-07',fill=4)
q=site('Collapsed pump annex',[(294,28),(360,28),(360,60),(344,60),(344,116),(294,116)],3,0)
hatch(q,302,36,14,14)
q.polygon([(324,36),(350,34),(352,47),(339,53),(337,67),(325,60),(330,48)],fill=12)
q.line((326,38,345,50,329,60),fill=4);q.line((333,36,334,62),fill=5)
for x,y in ((324,69),(340,57),(318,60),(336,73)):q.polygon([(x,y),(x+4,y+1),(x+2,y+4)],fill=5)
tank(q,311,93,9);duct(q,[(324,82),(334,82),(334,102)])
q=site('Rail machine shop: L footprint',[(146,178),(202,178),(202,214),(240,214),(240,302),(146,302)],5,0,material="metal")
grating(q,155,188,34,17);fan(q,157,227);fan(q,157,256)
for y in (228,252,276):
 q.rectangle((196,y,224,y+8),fill=2,outline=5);q.line((199,y+2,221,y+2),fill=8)
duct(q,[(185,223),(185,286),(223,286)]);hatch(q,209,265,13,13)
q=site('Raised navigation roof: stepped landing works',[(266,180),(322,180),(322,174),(350,174),(350,206),(356,206),(356,270),(342,270),(342,296),(266,296)],8,1,[252,168,374,316])
hatch(q,275,187,22,17);fan(q,324,187,15)
# A top-down maintenance landing circle, with restrained paint and a cross.
q.ellipse((282,218,331,267),outline=5,width=2);q.line((300,232,300,252),fill=5,width=2);q.line((292,242,309,242),fill=5,width=2)
q.text((310,272),'02',fill=4);duct(q,[(277,278),(277,208),(309,208)])
q=site('Courtyard assembly works: U footprint',[(146,350),(268,350),(268,472),(232,472),(232,398),(186,398),(186,472),(146,472)],4,0,roof=13)
fan(q,156,363);fan(q,239,363);duct(q,[(179,364),(223,364),(223,384)])
for y in (408,432):hatch(q,154,y,18,14);grating(q,242,y,15,16)
q.line((191,381,220,381),fill=5);q.line((191,384,220,384),fill=2)
q=site('Raised tank mill: staggered perimeter',[(284,356),(338,356),(338,368),(358,368),(358,446),(344,446),(344,464),(284,464)],6,1,[274,344,374,484],roof=4)
tank(q,303,386,12);tank(q,336,416,13);duct(q,[(300,405),(300,438),(328,438)]);grating(q,292,445,35,10);hatch(q,320,370,13,12)
# Paving/fencing is ground, never an architectural duplicate beneath a raised
# roof. These empty plots contain no matching facade or shadow to shear apart.
for yard in ([252,168,374,316],[274,344,374,484]):
 x,y,r,b=yard
 for yy in range(y+10,b-5,24):d.line((x+2,yy,r-3,yy),fill=13)
for x,y in ((247,226),(278,386)):
 d.line((x,y,x,y+42),fill=3)
 for yy in range(y,y+43,6):d.line((x-1,yy,x+1,yy+2),fill=4)
# Partial neighboring compounds make a city beyond the actual crop; none of
# this introduces additional logical world width or a repeating 320px strip.
for x in (14,414):
 for y in (18,186,354):
  q=body(base,[(x,y),(x+77,y),(x+87,y+12),(x+87,y+112),(x,y+112)],4)
  fan(q,x+13,y+24);hatch(q,x+48,y+20,20,21);grating(q,x+14,y+68,54,25)
# Ground details around the courtyard and junctions stay sparse and low-value.
for x,y in ((212,426),(249,279),(287,134)):
 d.rectangle((x,y,x+9,y+7),fill=2,outline=4);d.line((x+2,y+2,x+7,y+2),fill=5)
def encode(im,offset):
 chars=[];ids={};words=[]
 for ty in range(64):
  for tx in range(64):
   b=im.crop((tx*8,ty*8,tx*8+8,ty*8+8)).tobytes()
   if b not in ids:ids[b]=len(chars);chars.append(b)
   words.append(0x1000+offset//32+ids[b]*2)
 return b''.join(chars),struct.pack('>4096H',*words)
bc,bm=encode(base,0);rc,rm=encode(raised,65536)
assert len(bc)<=65536 and len(rc)<=40960
assert not ({10,11}&set(bc+rc)) and not any(v==0 for v in bc)
for n,b in [('WCELL.BIN',bc),('WMAP.BIN',bm),('WROOF.BIN',rc),('WRMAP.BIN',rm)]: (A/n).write_bytes(b)
p=A/'manifest.json';m=json.loads(p.read_text())
for n in ('WCELL.BIN','WMAP.BIN','WROOF.BIN','WRMAP.BIN'):
 b=(A/n).read_bytes();m['files'][n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
m['tiles']=len(bc)//64;m['roof_tiles']=len(rc)//64;m['vdp2_payload_bytes']=len(bc)+len(rc)+16384
m['aerial_city']={'width':512,'height':512,'crop_x':96,'roof_rate':[9,8],'sites':sites,'max_roof_offset':6}
p.write_text(json.dumps(m,indent=2)+'\n')
(R/'src/wingsuit_aerial_data.h').write_text('/* Generated by tools/build-topdown-city-v2.py. */\n#ifndef MF_WS_AERIAL_DATA_H\n#define MF_WS_AERIAL_DATA_H\n#define MF_WS_GROUND_BYTES %d\n#define MF_WS_ROOF_BYTES %d\n#define MF_WS_ROOF_OFFSET 65536\n#define MF_WS_ROOF_MAP_OFFSET 8192\n#define MF_WS_ROOF_NUMERATOR 9\n#define MF_WS_ROOF_DENOMINATOR 8\n#endif\n'%(len(bc),len(rc)))
base.convert('RGB').save(O/'ground-map.png');raised.convert('RGB').save(O/'complete-roof-map.png')
def view(cam,scroll):
 out=Image.new('RGB',(224,240));bp=base.load();rp=raised.load();px=out.load()
 # Integral review raster; runtime keeps the full 16.16 fractional component.
 roof_delta=(cam-48)/8
 for y in range(240):
  sy=(y-scroll)%512
  for x in range(224):
   bx=96+cam+x;rx=int(bx+roof_delta);v=rp[rx,sy] or bp[bx,sy];px[x,y]=rgb[v]
 return out
contact=Image.new('RGB',(3*224,4*256),(9,13,22));labels=ImageDraw.Draw(contact)
for row,scroll in enumerate((0,128,256,384)):
 for col,cam in enumerate((0,48,96)):
  im=view(cam,scroll);im.resize((448,480),Image.Resampling.NEAREST).save(O/f'host-view-{cam}-{scroll}.png')
  contact.paste(im,(col*224,row*256+16));labels.text((col*224+4,row*256+2),f'CAM {cam} / SCROLL {scroll}',fill=(146,154,160))
contact.save(O/'host-contact-sheet.png')
# Simple panning review animation, explicitly a host asset composite.
frames=[view(c,256).resize((448,480),Image.Resampling.NEAREST) for c in list(range(0,97,2))+list(range(94,0,-2))]
frames[0].save(O/'host-pan.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False)
print(json.dumps({'ground_tiles':len(bc)//64,'roof_tiles':len(rc)//64,'vdp2_payload':m['vdp2_payload_bytes']}))
