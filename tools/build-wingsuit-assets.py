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
 def player(d,a=actor):
  # Pixel-authored at the native 32x32 footprint; light comes from upper left.
  ink=(7,13,23);seam=(37,52,72)
  shade=(78,103,131) if not a else (20,30,45)
  mid=(154,177,201) if not a else (39,56,78)
  light=(218,232,238) if not a else (78,107,135)
  shine=(250,250,234) if not a else (153,187,205)
  trim=(203,67,59) if not a else (64,175,194)
  if not a:
   outer=[(13,7),(19,7),(23,10),(30,14),(31,19),(25,19),(22,18),(22,24),(20,29),(17,29),(16,24),(15,29),(11,29),(9,23),(9,18),(4,20),(0,19),(1,15),(8,11)]
   wing=[(11,10),(7,13),(2,16),(2,18),(9,16),(11,21),(14,23),(18,23),(21,20),(22,15),(29,18),(29,16),(22,12),(20,9)]
  else:
   outer=[(13,7),(19,7),(22,11),(27,14),(29,18),(26,20),(21,17),(21,24),(20,29),(18,29),(16,24),(14,29),(11,29),(10,23),(10,18),(6,20),(3,18),(5,14),(10,11)]
   wing=[(12,10),(8,14),(5,17),(6,18),(11,15),(12,22),(15,23),(18,22),(20,15),(26,18),(27,17),(21,12),(19,9)]
  d.polygon(outer,fill=ink);d.polygon(wing,fill=mid)
  d.polygon([(3+a*2,17),(10,14),(12,17),(13,22),(10,19),(9,17),(5,19)],fill=shade)
  d.polygon([(20,12),(25-a,15),(29-a*2,18),(25,17),(22,17),(21,21),(18,24),(17,19)],fill=shade)
  d.line([(3+a*2,16),(10,12),(13,10)],fill=shine)
  d.line([(20,10),(24,13),(28-a*2,16)],fill=light)
  d.line([(6+a,17),(11,14),(14,21)],fill=light)
  d.line([(19,20),(21,14),(26-a,17)],fill=seam)
  d.polygon([(11,10),(13,11),(15,22),(13,22)],fill=light)
  d.line([(12,10),(14,20)],fill=seam)
  d.line([(20,10),(18,23)],fill=ink)
  d.rectangle((12,22,19,24),fill=seam);d.line((12,22,19,22),fill=shine)
  d.rectangle((14,22,17,23),fill=(177,156,104))
  d.line((11,25,12,28),fill=shade);d.line((19,25,19,28),fill=shade)
  d.point((11,25),fill=light);d.point((19,25),fill=light)
  d.line((5+a,15,7+a,14),fill=trim);d.line((24-a,14,26-a,15),fill=trim)
  # Exposed head, temple/visor glint, and three distinct trailing hair locks.
  d.rectangle((12,3,20,7),fill=ink);d.rectangle((13,2,19,8),fill=(72,35,30))
  d.rectangle((13,4,19,7),fill=(182,108,75));d.line((13,4,18,4),fill=(247,194,136))
  d.point((12,6),fill=(211,139,92));d.point((20,6),fill=(211,139,92))
  d.line((14,5,18,5),fill=(29,53,73));d.point((14,5),fill=(133,221,225))
  hair_dark=(83,39,28) if not a else (68,42,29)
  hair_mid=(154,75,33) if not a else (128,80,37)
  hair_light=(232,148,65) if not a else (207,158,76)
  d.polygon([(13,7),(19,7),(20,11),(18,14),(20,18),(19,23),(17,20),(16,27),(14,24),(14,18),(11,23),(12,17),(12,12)],fill=hair_dark)
  d.polygon([(13,8),(15,9),(14,14),(13,18),(12,20),(13,14)],fill=hair_mid)
  d.polygon([(16,8),(18,9),(17,15),(18,19),(16,24),(15,21),(16,16)],fill=hair_mid)
  d.line([(14,8),(14,11),(13,16)],fill=hair_light)
  d.line([(17,9),(17,12),(16,17),(17,20)],fill=hair_light)
  d.point((19,19),fill=hair_mid);d.point((15,24),fill=hair_light)
 previews.append(sprite('WBUCK.BIN' if actor==0 else 'WCHUCK.BIN',(32,32),player))
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
manifest={'textures':6,'vdp1_bytes':7552,'tiles':len(tiles),'vdp2_payload_bytes':len(tiles)*64+8192,'cram_bytes':32,'max_sprite_commands':2+32+16+8,'files':files}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Review exports stay outside committed runtime assets.
w=R/'work';w.mkdir(exist_ok=True)
world.convert('RGB').resize((512,1024)).save(w/'wingsuit-city.png')
sheet=Image.new('RGBA',(128,32));x=0
for im in previews:sheet.paste(im,(x,0));x+=32
sheet.resize((768,192),Image.Resampling.NEAREST).save(w/'wingsuit-sprites.png')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))
