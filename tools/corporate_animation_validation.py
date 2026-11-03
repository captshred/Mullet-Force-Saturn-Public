"""Validate native animation pixels against shared indexed Saturn exports."""
from pathlib import Path
from PIL import Image,ImageChops
import json,struct,hashlib

def validate_corporate_animation(root,files=None):
 a=root/'assets/corporate-punk-animation';m=json.loads((a/'manifest.json').read_text());master=Image.open(root/'assets/corporate-punk/corporate-punk-84.png').convert('RGBA');pal=(root/'assets/corporate-punk/palette.bgr24').read_bytes();decoded=[];keys=set()
 used=set(Image.open(root/'assets/corporate-punk/corporate-punk-84.png').getdata())
 for r in m['resources']:
  b=(a/r['name']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];w,h=struct.unpack_from('<HH',b,12)
  assert b[:3]==b'\0\1\1' and b[7]==24 and b[16:18]==b'\10\0' and b[18:786]==pal and w%8==h%2==0 and len(b)==786+w*h
  assert set(b[786:])<=used and r['bytes']==(w*h+31)&~31
  key=(w,h,b[786:]);assert key not in keys;keys.add(key)
  q=Image.new('P',(w,h));q.putpalette([v for i in range(256) for v in pal[i*3:i*3+3][::-1]]);q.putdata([v for y in range(h-1,-1,-1) for v in b[786+y*w:786+(y+1)*w]]);q.info['transparency']=0;decoded.append(q.convert('RGBA'))
  if files is not None:assert files[r['name']]==b
 def visible(q):
  bg=Image.new('RGBA',q.size,(0,0,0,255));bg.alpha_composite(q);return bg.convert('RGB')
 poses=[]
 for f in m['poses']:
  expected=Image.open(a/(f['name']+'.png')).convert('RGBA');assert expected.size==(96,96) and expected.getbbox()[1]==8 and expected.getbbox()[3]==92 and set(expected.getchannel('A').getdata())=={0,255}
  for flip in [False,True]:
   out=Image.new('RGBA',(96,96));occupied=set()
   for p in f['parts']:
    q=decoded[p['resource']];assert q.size==(p['width'],p['height'])
    for y in range(q.height):
     for x in range(q.width):
      if q.getpixel((x,y))[3]:assert (x+p['x'],y+p['y']) not in occupied;occupied.add((x+p['x'],y+p['y']))
    if flip:q=q.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    out.alpha_composite(q,(96-p['x']-p['width'] if flip else p['x'],p['y']))
   ref=expected.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else expected
   assert out.getchannel('A').tobytes()==ref.getchannel('A').tobytes() and visible(out).tobytes()==visible(ref).tobytes()
  poses.append(expected)
 assert poses[0].tobytes()==master.tobytes() and poses[4].tobytes()==master.tobytes()
 for f in [1,2]:
  assert poses[f].crop((0,49,96,96)).tobytes()==master.crop((0,49,96,96)).tobytes()
  assert poses[f].crop((0,0,96,24)).tobytes()==master.crop((0,0,96,24)).tobytes()
  assert poses[f].tobytes()!=master.tobytes()
 for f in [3,5]:assert poses[f].crop((0,0,96,49)).tobytes()==master.crop((0,0,96,49)).tobytes()
 assert len({q.tobytes() for q in poses[3:]})==3
 assert m['texture_bytes']==sum(r['bytes'] for r in m['resources'])==14016 and m['texture_slots']==len(decoded)==9
 assert m['boot_bytes']==365120 and m['boot_free']==93368 and m['boot_slots']==134 and m['full_free']==17368
 # First pose exports are exactly the approved TGAs, not reinterpreted artwork.
 for i in range(3):assert (a/f'CP{i:02d}.TGA').read_bytes()==(root/f'assets/corporate-punk/CP{i}.TGA').read_bytes()
 for label in ['idle','walk']:
  gif=Image.open(a/f'{label}-4x.gif');assert gif.n_frames==3
 print('PASS Corporate Punk: exact approved idle1/TGAs, fixed idle feet/head, locked walk upper body, 3 distinct steps, palette, native/mirrored seam-free assembly, 9 deduplicated resources /14016 bytes')
 return m
if __name__=='__main__':validate_corporate_animation(Path(__file__).resolve().parents[1])
