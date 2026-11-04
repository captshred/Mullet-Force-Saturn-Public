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
 save(name,b''.join(struct.pack('>H',rgb(p) if p[3] else 0) for p in im.getdata()))
 return im
previews=[]
for actor in range(2):
 def player(d,a=actor):
  suit=(175,188,204) if not a else (36,46,68); edge=(83,113,145) if not a else (83,100,125)
  d.polygon([(15,5),(12,9),(2,15),(1,20),(10,19),(12,25),(20,25),(22,19),(30,20),(29,15),(20,9),(18,5)],fill=(10,17,31))
  d.polygon([(13,9),(4,16),(3,18),(12,16),(14,23),(18,23),(20,16),(28,18),(27,16),(19,9)],fill=suit)
  d.line([(4,17),(12,14),(15,22)],fill=edge);d.line([(27,17),(20,14),(17,22)],fill=edge)
  d.rectangle((14,4,18,8),fill=(231,170,121));d.rectangle((13,3,19,5),fill=(108,55,33))
  d.polygon([(13,7),(14,11),(13,17),(15,15),(16,20),(18,16),(19,9),(18,7)],fill=(154,80,40))
  d.line((15,9,15,15),fill=(220,139,64));d.rectangle((12,23,14,27),fill=(62,72,93));d.rectangle((18,23,20,27),fill=(62,72,93))
  d.point((15,6),fill=(255,219,168));d.point((18,6),fill=(255,219,168))
 previews.append(sprite('WBUCK.BIN' if actor==0 else 'WCHUCK.BIN',(32,32),player))
def drone(d):
 d.ellipse((0,2,8,9),fill=(28,49,62));d.ellipse((15,2,23,9),fill=(28,49,62));d.ellipse((0,14,8,21),fill=(28,49,62));d.ellipse((15,14,23,21),fill=(28,49,62))
 for x,y in [(4,5),(19,5),(4,17),(19,17)]:d.line((x-3,y,x+3,y),fill=(99,159,173));d.line((x,y-2,x,y+2),fill=(99,159,173))
 d.polygon([(8,6),(15,6),(18,12),(14,18),(9,18),(5,12)],fill=(107,127,141));d.rectangle((9,8,14,14),fill=(28,36,57));d.rectangle((10,12,13,15),fill=(255,60,90));d.line((9,7,14,7),fill=(214,182,59))
previews.append(sprite('WDRONE.BIN',(24,24),drone))
def bullet(d):d.rectangle((3,0,4,7),fill=(255,227,101));d.rectangle((3,0,4,4),fill=(232,255,255))
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
