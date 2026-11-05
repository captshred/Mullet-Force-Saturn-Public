#!/usr/bin/env python3
"""Generate original prototype pixel art and deduplicated 8-bit overhead tiles."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]; O=R/'assets/wingsuit';O.mkdir(exist_ok=True)
files={}
def save(name,data):
 (O/name).write_bytes(data);files[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def rgb(c):return 0 if c is None else 0x8000|(c[0]>>3)|((c[1]>>3)<<5)|((c[2]>>3)<<10)
def sprite(name,size,paint):
 im=Image.new('RGBA',size);d=ImageDraw.Draw(im);paint(d)
 pixels=im.tobytes()
 save(name,b''.join(struct.pack('>H',rgb(pixels[i:i+3]) if pixels[i+3] else 0) for i in range(0,len(pixels),4)))
 return im
previews=[]
for actor in range(2):
 for bank,suffix in [(0,''),(-1,'L'),(1,'R')]:
  def player(d,a=actor,b=bank):
   # Pose-specific anatomy: lowered near wing, narrowed raised wing and a
   # curved spine. Skin/head, chest, hips and two legs remain separate.
   ink=(7,14,24);dark=(43,63,83) if not a else (16,25,37)
   mid=(145,171,195) if not a else (37,53,73)
   light=(214,231,238) if not a else (83,115,139)
   glint=(250,247,220) if not a else (161,192,205)
   accent=(205,64,54) if not a else (52,170,187)
   def poly(points,color):d.polygon(points,fill=color)
   # Downward tilt on the banking side, torso leans into the turn. Right/left
   # use different folds and lighting, rather than flipping a rendered bitmap.
   cx=16+b;head=16+b;left_y=14+(3 if b<0 else -1 if b>0 else 0)
   right_y=14+(3 if b>0 else -1 if b<0 else 0)
   lx=(1 if not a else 3)+(2 if b>0 else 0)
   rx=(30 if not a else 28)-(2 if b<0 else 0)
   poly([(cx-5,8),(cx+4,8),(rx,right_y),(rx-1,right_y+4),(cx+5,17),
         (cx+4,23),(cx+1,26),(cx-4,24),(cx-6,17),(lx+1,left_y+4),(lx,left_y)],ink)
   poly([(cx-4,9),(cx-7,12),(lx+1,left_y+1),(lx+2,left_y+3),(cx-5,15),(cx-3,20)],mid)
   poly([(cx+3,9),(cx+7,12),(rx-1,right_y+1),(rx-2,right_y+3),(cx+4,15),(cx+2,20)],dark if b<0 else mid)
   d.line([(cx-4,9),(lx+2,left_y+1)],fill=glint)
   d.line([(cx+3,9),(rx-2,right_y+1)],fill=light)
   d.line([(cx-6,12),(cx-4,17)],fill=dark)
   d.line([(cx+6,12),(cx+3,17)],fill=light if b>0 else ink)
   # Exposed hands make the arm ends human rather than aircraft wing tips.
   d.rectangle((lx,left_y,lx+1,left_y+1),fill=(225,164,111))
   d.rectangle((rx-1,right_y,rx,right_y+1),fill=(184,113,76))
   poly([(cx-3,9),(cx+2,9),(cx+3,17),(cx+1,21),(cx-3,20),(cx-4,15)],mid)
   d.line((cx-3,10,cx-2,17),fill=glint)
   d.line((cx+2,10,cx+2,18),fill=dark)
   d.line((cx-3,13,cx+2,16),fill=dark)
   d.point((cx-2,12),fill=accent);d.point((cx+1,12),fill=accent)
   d.line((cx-3,20,cx+2,20),fill=glint)
   d.rectangle((cx-1,20,cx,21),fill=(177,145,79))
   # Separate hips, thighs and boots with a transparent gap, no long hair
   # column covering the chest or lower body.
   poly([(cx-3,21),(cx-1,22),(cx-2-b,27),(cx-4-b,29),(cx-5-b,28)],ink)
   d.line((cx-3,22,cx-3-b,26),fill=light)
   poly([(cx+1,21),(cx+3,22),(cx+4-b,28),(cx+2-b,29),(cx-b,26)],ink)
   d.line((cx+2,22,cx+2-b,26),fill=mid)
   # Small bare head/ears above the shoulders. Keep warm face pixels distinct
   # from the short crown and two wind-swept mullet locks behind the neck.
   d.rectangle((head-3,2,head+2,7),fill=ink)
   d.rectangle((head-2,3,head+1,6),fill=(211,147,101))
   d.line((head-2,3,head+1,3),fill=(251,206,154))
   d.point((head-3,5),fill=(225,163,110));d.point((head+2,5),fill=(182,114,80))
   d.line((head-1,4,head+1,4),fill=(93,55,36))
   hair=(141,72,34) if not a else (116,77,37)
   hair_hi=(224,143,59) if not a else (207,162,80)
   hair_dark=(71,36,26)
   d.line((head-2,2,head+1,2),fill=hair_dark)
   poly([(head-2,6),(head+1,6),(head+2,9),(head+2-b*2,12),
         (head-b*2,16),(head-1-b*2,12),(head-3-b*2,14),(head-2,9)],hair_dark)
   d.line([(head-2,7),(head-2,10),(head-3-b*2,13)],fill=hair)
   d.line([(head,7),(head+1,10),(head-b*2,14)],fill=hair)
   d.line([(head-1,7),(head,10),(head-1-b*2,12)],fill=hair_hi)
   # Red/cyan wing seams remain side-specific in all poses.
   d.line((lx+3,left_y+1,lx+4,left_y+1),fill=accent)
   d.point((rx-4,right_y+2),fill=accent)
  im=sprite(('WBUCK' if actor==0 else 'WCHUCK')+suffix+'.BIN',(32,32),player)
  previews.append(im)
def drone(d):
 ink=(6,15,25);dark=(28,43,58);steel=(85,111,129);lit=(158,189,201)
 # Four rotor pods, chamfered plating, struts and a corporate red sensor.
 d.line((4,4,19,19),fill=dark,width=4);d.line((19,4,4,19),fill=dark,width=4)
 d.line((5,4,18,18),fill=steel);d.line((18,4,5,18),fill=steel)
 for x,y in [(4,4),(19,4),(4,19),(19,19)]:
  d.ellipse((x-4,y-4,x+4,y+4),fill=ink)
  d.arc((x-4,y-4,x+3,y+3),170,310,fill=lit)
  d.arc((x-3,y-3,x+4,y+4),0,130,fill=steel)
  d.ellipse((x-2,y-2,x+2,y+2),fill=dark)
  d.line((x-3,y,x+3,y),fill=(66,132,150));d.line((x,y-2,x,y+2),fill=(123,178,188))
  d.point((x,y),fill=(211,225,216));d.point((x+3,y+3),fill=(43,72,91))
 d.polygon([(8,5),(15,5),(19,10),(18,16),(14,19),(9,18),(5,13),(5,9)],fill=ink)
 d.polygon([(8,6),(14,6),(17,9),(16,15),(13,17),(9,16),(6,12),(6,10)],fill=steel)
 d.polygon([(8,6),(14,6),(16,8),(9,8),(7,12),(6,11)],fill=lit)
 d.polygon([(15,8),(18,11),(16,16),(13,17),(13,14)],fill=(47,66,84))
 d.rectangle((9,9,14,14),fill=(18,30,44));d.line((9,9,13,9),fill=(224,216,163))
 d.rectangle((10,10,13,11),fill=(123,31,54));d.rectangle((10,12,13,14),fill=(236,49,76))
 d.line((10,12,12,12),fill=(255,166,139));d.point((11,13),fill=(255,225,183))
 d.line((9,16,13,16),fill=(217,171,67));d.point((10,16),fill=ink);d.point((13,16),fill=ink)
 d.line((7,10,7,12),fill=(45,64,77));d.point((15,7),fill=(236,224,174))
previews.append(sprite('WDRONE.BIN',(24,24),drone))
def bullet(d):
 d.line((2,2,2,6),fill=(53,139,163));d.line((5,2,5,6),fill=(53,139,163))
 d.rectangle((3,0,4,6),fill=(255,204,77));d.rectangle((3,0,4,3),fill=(240,255,247))
 d.point((3,7),fill=(196,107,44));d.point((4,7),fill=(196,107,44))
sprite('WSHOT.BIN',(8,8),bullet)
def hostile(d):d.ellipse((1,1,6,6),fill=(244,57,109));d.rectangle((3,2,4,5),fill=(255,213,177))
sprite('WHOST.BIN',(8,8),hostile)
def explosion(d):
 d.polygon([(16,1),(19,10),(28,6),(23,15),(31,20),(21,22),(19,31),(13,24),(4,29),(8,20),(0,14),(10,12),(7,3)],fill=(215,60,51))
 d.ellipse((7,8,25,25),fill=(255,156,55));d.ellipse((11,11,21,21),fill=(255,239,166))
previews.append(sprite('WBOOM.BIN',(32,32),explosion))
colors=[(8,13,26),(20,29,43),(33,46,61),(47,62,76),(64,83,97),(91,114,128),(134,151,154),(208,178,76),(35,104,124),(50,168,178),(183,55,125),(244,112,164),(14,20,32),(28,37,48),(71,88,103),(166,209,216)]
world=Image.new('P',(256,512));world.putpalette(sum((list(c) for c in colors),[])+[0]*(768-48));d=ImageDraw.Draw(world)
d.rectangle((0,0,255,511),fill=1)
for y in range(0,512,128):
 d.rectangle((0,y+104,255,y+127),fill=2);d.line((0,y+115,255,y+115),fill=7)
 for bx in (8,152):
  d.rectangle((bx,y+8,bx+94,y+94),fill=0);d.rectangle((bx,y+8,bx+87,y+87),fill=4)
  d.rectangle((bx+4,y+12,bx+83,y+83),fill=3);d.line((bx+4,y+12,bx+83,y+12),fill=6)
  for vy in (24,56):
   d.rectangle((bx+16,y+vy,bx+39,y+vy+15),fill=1);d.rectangle((bx+16,y+vy,bx+35,y+vy+11),fill=5)
   for k in range(3):d.line((bx+18,y+vy+2+k*3,bx+33,y+vy+2+k*3),fill=2)
  d.line((bx+56,y+16,bx+56,y+71),fill=6);d.line((bx+59,y+16,bx+59,y+71),fill=2)
  if y%256==0:d.rectangle((bx+64,y+78,bx+79,y+81),fill=10);d.line((bx+65,y+78,bx+78,y+78),fill=11)
  else:
   d.rectangle((bx+64,y+40,bx+79,y+71),fill=2)
   for py in range(44,72,8):d.line((bx+64,y+py,bx+76,y+py),fill=6)
d.rectangle((112,0,143,511),fill=2)
for y in range(0,512,32):d.rectangle((127,y+4,128,y+19),fill=7)
d.line((114,0,114,511),fill=5);d.line((141,0,141,511),fill=5)
for y in range(104,512,128):
 for x in range(116,140,8):d.rectangle((x,y+3,x+3,y+20),fill=6)
tiles=[];lookup={};mapping=[]
for ty in range(64):
 for tx in range(64):
  t=world.crop(((tx%32)*8,ty*8,(tx%32)*8+8,ty*8+8)).tobytes()
  if t not in lookup:lookup[t]=len(tiles);tiles.append(t)
  mapping.append(0x1000+lookup[t]*2)
save('WCELL.BIN',b''.join(tiles));save('WMAP.BIN',struct.pack('>4096H',*mapping));save('WPAL.BIN',b''.join(struct.pack('>H',rgb(c)) for c in colors))
assert len(tiles)*64<=16384
manifest={'textures':10,'vdp1_bytes':15744,'tiles':len(tiles),'vdp2_payload_bytes':len(tiles)*64+8192,'cram_bytes':32,'max_sprite_commands':2+32+16+8,'files':files}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Review exports stay outside committed runtime assets.
w=R/'work';w.mkdir(exist_ok=True)
world.convert('RGB').resize((512,1024)).save(w/'wingsuit-city.png')
sheet=Image.new('RGBA',(256,32));x=0
for im in previews:sheet.paste(im,(x,0));x+=32
sheet.resize((1536,192),Image.Resampling.NEAREST).save(w/'wingsuit-sprites.png')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))
